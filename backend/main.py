# backend/main.py
import os
import sys
import torch
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from collections import deque
import asyncio
import joblib
import random # --- ADDED: Import the random library ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from sensors import sensors
from sensors.sensors import global_sensor_state
from ml_model.sensors.cnn_model import CNNModel

try:
    from ml_model.weather.infer_weather import WeatherForecaster, WEATHER_FEATURES, WEATHER_WINDOW_SIZE
except ImportError:
    print("⚠️ Weather model files not found. Weather forecasting disabled.")
    WeatherForecaster = lambda: type('obj', (object,), {'is_ready': False})
    WEATHER_FEATURES = []
    WEATHER_WINDOW_SIZE = 50

CNN_WINDOW_SIZE = 50
CNN_NUM_FEATURES = 11
cnn_data_buffer = deque(maxlen=CNN_WINDOW_SIZE)
CNN_MODEL_PATH = os.path.join(BASE_DIR, "ml_model", "sensors", "best_cnn_model.pth")
CNN_SCALER_PATH = os.path.join(BASE_DIR, "ml_model", "sensors", "scaler.pkl")

weather_data_buffer = deque(maxlen=WEATHER_WINDOW_SIZE)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load CNN model & scaler
cnn_model, cnn_scaler = None, None
if os.path.exists(CNN_MODEL_PATH):
    cnn_model = CNNModel(num_features=CNN_NUM_FEATURES, num_classes=2)
    try:
        dummy_input = torch.randn(1, CNN_WINDOW_SIZE, CNN_NUM_FEATURES)
        cnn_model(dummy_input)
    except Exception as e:
        print(f"Error dummy forward: {e}")
    cnn_model.load_state_dict(torch.load(CNN_MODEL_PATH, map_location=device))
    cnn_model.to(device)
    cnn_model.eval()
    print("✅ Rockfall CNN model loaded.")
    if os.path.exists(CNN_SCALER_PATH):
        cnn_scaler = joblib.load(CNN_SCALER_PATH)
        print("✅ Rockfall CNN scaler loaded.")
    else:
        print("⚠️ CNN scaler not found.")
else:
    print("⚠️ Rockfall CNN model not found.")

weather_forecaster = WeatherForecaster()

# --- ADDED: Helper function for dynamic weather forecast simulation ---
def simulate_weather_forecast(current_readings: dict, steps: int = 5) -> list:
    """Generates a simple, dynamic weather forecast for visualization."""
    forecast = []
    last_temp = current_readings.get("temperature_celsius", 28.0)
    last_hum = current_readings.get("humidity_percent", 65.0)
    last_rain = current_readings.get("rain_sensor_mmhr", 0.0)

    for _ in range(steps):
        next_temp = last_temp + random.uniform(-0.5, 0.5)
        next_hum = last_hum + random.uniform(-2, 2)
        if last_rain > 1:
            next_rain = last_rain + random.uniform(-2, 1)
        else:
            next_rain = random.choices([0, 0, 0, 0, 1.5, 3.0], k=1)[0]
        next_rain = max(0, next_rain)
        forecast.append([next_rain, next_temp, next_hum])
        last_temp, last_hum, last_rain = next_temp, next_hum, next_rain
        
    return forecast

app = FastAPI(title="TRINETRA - Geological Event Monitoring API")

allowed_origins = [
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:3000", "http://127.0.0.1:3000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ... (All your HTTP endpoints like /api/status, /api/trigger_event, etc. remain exactly the same) ...
SENSOR_GROUPS = { "Seismic": ["accelerometer", "geophone", "seismometer"], "Displacement": ["crack_sensor", "inclinometer", "extensometer"], "Hydro": ["moisture_sensor", "piezometer"], "Environmental": ["rain_sensor_mmhr", "temperature_celsius", "humidity_percent"] }
@app.get("/api/sensor_groups")
async def get_sensor_groups(): return JSONResponse(SENSOR_GROUPS)
@app.get("/api/sensors")
async def get_current_sensors():
    try:
        readings = sensors.get_all_readings()
        return JSONResponse(readings)
    except Exception as e:
        return JSONResponse({"error": "failed to read sensors", "detail": str(e)}, status_code=500)
@app.get("/api/status")
async def get_status(): 
    return { 
        "cnn_loaded": cnn_model is not None and cnn_scaler is not None, 
        "weather_ready": getattr(weather_forecaster, "is_ready", False) 
    }

# Alert system endpoints
@app.get("/alert")
async def get_alert_status():
    """Get current alert status for the RiskIndicator component"""
    try:
        # Check if there's an active event and determine alert level
        if global_sensor_state["event_active"]:
            if global_sensor_state["phase"] == "main_event":
                return {"mode": "emergency", "location": "TRINETRA Monitoring Zone"}
            elif global_sensor_state["phase"] == "danger":
                return {"mode": "emergency", "location": "TRINETRA Monitoring Zone"}
            elif global_sensor_state["phase"] == "warning":
                return {"mode": "warning", "location": "TRINETRA Monitoring Zone"}
            elif global_sensor_state["phase"] == "normal":
                return {"mode": "safe", "location": "TRINETRA Monitoring Zone"}
        
        # Check ML prediction for normal operation
        if len(cnn_data_buffer) == CNN_WINDOW_SIZE and cnn_model and cnn_scaler:
            window_data = np.array(cnn_data_buffer)
            scaled_window = cnn_scaler.transform(window_data)
            input_tensor = torch.tensor(scaled_window, dtype=torch.float32).unsqueeze(0).to(device)
            with torch.no_grad():
                logits = cnn_model(input_tensor)
                probs = torch.softmax(logits, dim=1)
                confidence, pred_idx = torch.max(probs, dim=1)
                if pred_idx.item() == 1 and confidence.item() > 0.7:
                    return {"mode": "warning", "location": "TRINETRA Monitoring Zone"}
        
        return {"mode": "safe", "location": "TRINETRA Monitoring Zone"}
    except Exception as e:
        print(f"Error in alert endpoint: {e}")
        return {"mode": "safe", "location": "TRINETRA Monitoring Zone"}

@app.post("/alert/{mode}")
async def set_alert_mode(mode: str):
    """Set alert mode manually"""
    if mode not in ["safe", "warning", "emergency"]:
        raise HTTPException(status_code=400, detail="Invalid mode")
    return {"mode": mode, "location": "TRINETRA Monitoring Zone"}
@app.post("/api/trigger_event/{event_type}")
async def trigger_event_now(event_type: str):
    if event_type not in ["rockfall", "rainfall", "landslide"]:
        raise HTTPException(status_code=400, detail="Invalid event type")
    sensors.trigger_all(event_type=event_type, duration_s=60)
    return {"message": f"{event_type} event triggered for 60s"}


@app.websocket("/ws/live")
async def websocket_live(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            readings = sensors.get_all_readings()

            # Prepare CNN input
            cnn_features = [readings[k] for k in ["accelerometer", "geophone", "seismometer", "moisture_sensor", "piezometer", "crack_sensor", "inclinometer", "extensometer", "rain_sensor_mmhr", "temperature_celsius", "humidity_percent"]]
            cnn_data_buffer.append(cnn_features)
            prediction_label, confidence_val = None, 0.0
            if cnn_model and cnn_scaler and len(cnn_data_buffer) == CNN_WINDOW_SIZE:
                window_data = np.array(cnn_data_buffer)
                scaled_window = cnn_scaler.transform(window_data)
                input_tensor = torch.tensor(scaled_window, dtype=torch.float32).unsqueeze(0).to(device)
                with torch.no_grad():
                    logits = cnn_model(input_tensor)
                    probs = torch.softmax(logits, dim=1)
                    confidence, pred_idx = torch.max(probs, dim=1)
                    prediction_label = "Event Detected" if pred_idx.item() == 1 else "Normal"
                    confidence_val = round(confidence.item(), 4)

            # --- UPDATED: Weather forecasting section ---
            forecast_data = None
            if getattr(weather_forecaster, "is_ready", False):
                # If the real model is ready, use it
                weather_features = [readings[k] for k in WEATHER_FEATURES]
                weather_data_buffer.append(weather_features)
                if len(weather_data_buffer) == WEATHER_WINDOW_SIZE:
                    weather_window = np.array(weather_data_buffer)
                    forecast_data = weather_forecaster.forecast_from_window(weather_window).tolist()
            else:
                # If the real model is not ready, use our new simulation
                forecast_data = simulate_weather_forecast(readings)

            readings["prediction"] = prediction_label
            readings["confidence"] = confidence_val
            readings["weather_forecast"] = forecast_data

            await ws.send_json(readings)
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}", file=sys.stderr)
        try:
            await ws.close()
        except Exception:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)