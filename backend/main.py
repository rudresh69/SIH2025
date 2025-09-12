"""
main.py
FastAPI server with multi-chart live sensor visualization,
real-time ML predictions for rockfall, and weather nowcasting.

This is the final, integrated version combining both the original CNN model
and the new LSTM weather forecasting model.
"""

import os
import sys
import torch
import numpy as np
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from collections import deque
import asyncio
import joblib

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# --- IMPORT LOCAL MODULES ---
from sensors import sensors
from ml_model.sensors.cnn_model import CNNModel
# --- MODIFIED ---: Import the weather forecaster and its specific configs
# Assuming the weather model files are in the specified path.
try:
    from ml_model.weather.infer_weather import WeatherForecaster, WEATHER_FEATURES, WEATHER_WINDOW_SIZE
except ImportError:
    print("⚠️ Weather model files not found. Weather forecasting will be disabled.")
    WeatherForecaster = lambda: type('obj', (object,), {'is_ready': False})
    WEATHER_FEATURES = []
    WEATHER_WINDOW_SIZE = 50


# ===================================================================
# 1. CONFIGURATION & GLOBAL STATE ⚙️
# ===================================================================

# --- Rockfall Prediction (CNN) Config ---
CNN_WINDOW_SIZE = 50
CNN_NUM_FEATURES = 11
cnn_data_buffer = deque(maxlen=CNN_WINDOW_SIZE)
CNN_MODEL_PATH = os.path.join(BASE_DIR, "ml_model", "sensors", "best_cnn_model.pth")
CNN_SCALER_PATH = os.path.join(BASE_DIR, "ml_model", "sensors", "scaler.pkl")

# --- NEW: Weather Forecasting (LSTM) Config ---
weather_data_buffer = deque(maxlen=WEATHER_WINDOW_SIZE)

# ===================================================================
# 2. MODEL & SCALER LOADING 🧠
# ===================================================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- Load Rockfall CNN Model ---
cnn_model = None
cnn_scaler = None
if os.path.exists(CNN_MODEL_PATH):
    cnn_model = CNNModel(num_features=CNN_NUM_FEATURES, num_classes=2)

    # --- [FIX] Perform a dummy forward pass to initialize dynamic layers ---
    # This creates the `fc_layers` so the state dict can be loaded correctly.
    try:
        dummy_input = torch.randn(1, CNN_WINDOW_SIZE, CNN_NUM_FEATURES)
        cnn_model(dummy_input)
    except Exception as e:
        print(f"Error during dummy forward pass: {e}")
    # --------------------------------------------------------------------

    cnn_model.load_state_dict(torch.load(CNN_MODEL_PATH, map_location=device))
    cnn_model.to(device)
    cnn_model.eval()
    print("✅ Rockfall CNN model loaded successfully.")
    
    if os.path.exists(CNN_SCALER_PATH):
        cnn_scaler = joblib.load(CNN_SCALER_PATH)
        print("✅ Rockfall CNN scaler loaded successfully.")
    else:
        print(f"⚠️ CNN scaler not found at {CNN_SCALER_PATH}. Rockfall predictions may be inaccurate.")
else:
    print(f"⚠️ Rockfall CNN model not found at {CNN_MODEL_PATH}. Predictions will be disabled.")


# --- NEW: Load Weather LSTM Model ---
# The WeatherForecaster class handles loading its own model and scaler.
weather_forecaster = WeatherForecaster()

# ===================================================================
# 3. FRONTEND & API SETUP 🖥️
# ===================================================================
SENSOR_GROUPS = {
    "Seismic": ["accelerometer", "geophone", "seismometer"],
    "Displacement": ["crack_sensor", "inclinometer", "extensometer"],
    "Hydro": ["moisture_sensor", "piezometer"],
    "Environmental": ["rain_sensor_mmhr", "temperature_celsius", "humidity_percent"]
}

app = FastAPI(title="Rockfall & Weather Demo API")

# --- HTML & JavaScript for Frontend ---
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rockfall Live Demo</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 20px; background-color: #f4f7f6; }}
        h2, h3 {{ text-align: center; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .chart-box {{ background-color: #fff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); padding: 15px; margin-top: 20px; }}
        .status-container {{
            text-align: center; margin-top: 20px; padding: 15px;
            border-radius: 8px; transition: background-color 0.5s ease; color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        #prediction-container {{ background-color: #6c757d; font-size: 1.5em; }}
        #weather-container {{ background-color: #17a2b8; font-size: 1.1em; padding: 10px; margin-top: 10px; }}
        #controls {{ text-align: center; margin: 20px 0; }}
        button {{
            padding: 10px 20px; font-size: 1em; cursor: pointer; border: none;
            border-radius: 5px; background-color: #007bff; color: white;
            margin: 0 10px; transition: background-color 0.3s;
        }}
        button:hover {{ background-color: #0056b3; }}
    </style>
</head>
<body>
<div class="container">
    <h2>Live Sensor Data & Prediction</h2>

    <div id="prediction-container" class="status-container">
        <p id="prediction">STATUS: Awaiting data...</p>
    </div>
    
    <div id="weather-container" class="status-container">
        <h3 style="color: white; margin-top: 0;">Weather Forecast</h3>
        <p id="weather-forecast">Collecting data for forecast...</p>
    </div>

    <div id="controls">
        <button onclick="triggerEvent('rockfall')">Trigger Rockfall</button>
        <button onclick="triggerEvent('landslide')">Trigger Landslide</button>
        <button onclick="triggerEvent('rainfall')">Trigger Rainfall</button>
    </div>

    <div id="charts-container"></div>
</div>
<script>
    const ws = new WebSocket(`ws://${window.location.host}/ws/live`);
    const sensorGroups = {sensor_groups_json};
    const charts = {{}};
    const predElement = document.getElementById('prediction');
    const weatherElement = document.getElementById('weather-forecast');
    const chartsContainer = document.getElementById('charts-container');

    for (const group in sensorGroups) {{
        const chartBox = document.createElement('div');
        chartBox.className = 'chart-box';
        const canvas = document.createElement('canvas');
        canvas.id = group;
        chartBox.appendChild(canvas);
        chartsContainer.appendChild(chartBox);
        
        const ctx = canvas.getContext('2d');
        const datasets = sensorGroups[group].map(s => ({{
            label: s.replace(/_/g, ' ').replace(/(?:^|\\s)\\S/g, a => a.toUpperCase()),
            data: [],
            borderColor: `hsl(${{Math.random() * 360}}, 70%, 50%)`,
            fill: false, borderWidth: 2, pointRadius: 0
        }}));
        if (group === "Seismic") {{
            datasets.push({{
                label: "Event Label", data: [], borderColor: 'rgba(220, 53, 69, 0.7)',
                borderDash: [5, 5], fill: true, backgroundColor: 'rgba(220, 53, 69, 0.1)',
                borderWidth: 2, pointRadius: 0
            }});
        }}
        charts[group] = new Chart(ctx, {{
            type: 'line', data: {{ labels: [], datasets: datasets }},
            options: {{ 
                animation: false, 
                scales: {{ x: {{ title: {{ display: true, text: 'Time' }} }} }},
                plugins: {{ title: {{ display: true, text: group + ' Sensors', font: {{ size: 16 }} }} }}
            }}
        }});
    }}

    ws.onmessage = function(event) {{
        const msg = JSON.parse(event.data);
        const ts = msg.timestamp.slice(11, 23);

        for (const group in charts) {{
            const chart = charts[group];
            chart.data.labels.push(ts);
            if (chart.data.labels.length > 200) chart.data.labels.shift();
            
            chart.data.datasets.forEach(ds => {{
                const key = ds.label.toLowerCase().replace(/ /g, '_');
                if (key === "event_label") ds.data.push(msg.label * 5);
                else ds.data.push(msg[key]);
                if (ds.data.length > 200) ds.data.shift();
            }});
            chart.update();
        }}

        if (msg.prediction) {{
            predElement.innerText = `Prediction: ${msg.prediction} | Confidence: ${(msg.confidence * 100).toFixed(2)}%`;
            if (msg.prediction === "Event Detected") {{
                predElement.parentElement.style.backgroundColor = '#dc3545';
            }} else {{
                predElement.parentElement.style.backgroundColor = '#28a745';
            }}
        }} else {{
            predElement.parentElement.style.backgroundColor = '#6c757d';
            predElement.innerText = "STATUS: Collecting data for first prediction...";
        }}
        
        if (msg.weather_forecast) {{
            let forecastHTML = "<b>Next 5 Steps:</b><br>";
            msg.weather_forecast.forEach((step, i) => {{
                forecastHTML += `T+${i+1}: Rain: ${step[0].toFixed(1)}mm/h, Temp: ${step[1].toFixed(1)}°C, Hum: ${step[2].toFixed(1)}%<br>`;
            }});
            weatherElement.innerHTML = forecastHTML;
        }} else {{
            weatherElement.innerHTML = "Collecting data for first forecast...";
        }}
    }};

    function triggerEvent(eventType) {{
        fetch(`/trigger_event/${eventType}`, {{ method: 'POST' }})
          .then(res => res.json()).then(data => console.log(data.message));
    }}
</script>
</body>
</html>
""".replace("{sensor_groups_json}", str(SENSOR_GROUPS))


@app.get("/")
async def get():
    return HTMLResponse(html_template)


@app.websocket("/ws/live")
async def websocket_live(ws: WebSocket):
    await ws.accept()
    while True:
        try:
            readings = sensors.get_all_readings()

            # --- 1. Handle Rockfall CNN Prediction ---
            cnn_features = [readings[key] for key in [
                "accelerometer", "geophone", "seismometer", "moisture_sensor", "piezometer",
                "crack_sensor", "inclinometer", "extensometer", "rain_sensor_mmhr",
                "temperature_celsius", "humidity_percent"
            ]]
            cnn_data_buffer.append(cnn_features)

            prediction_label = None
            confidence_val = 0.0
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

            # --- 2. NEW: Handle Weather LSTM Forecast ---
            forecast_data = None
            if weather_forecaster.is_ready:
                weather_features = [readings[key] for key in WEATHER_FEATURES]
                weather_data_buffer.append(weather_features)
                
                if len(weather_data_buffer) == WEATHER_WINDOW_SIZE:
                    weather_window = np.array(weather_data_buffer)
                    forecast_values = weather_forecaster.forecast_from_window(weather_window)
                    forecast_data = forecast_values.tolist()

            # --- 3. Send combined data to frontend ---
            readings["prediction"] = prediction_label
            readings["confidence"] = confidence_val
            readings["weather_forecast"] = forecast_data
            
            await ws.send_json(readings)
            await asyncio.sleep(0.05)

        except Exception as e:
            print(f"An error occurred in the websocket loop: {e}")
            break


@app.post("/trigger_event/{event_type}")
async def trigger_event_now(event_type: str):
    if event_type not in ["rockfall", "rainfall", "landslide"]:
        raise HTTPException(status_code=400, detail="Invalid event type")
    sensors.trigger_all(event_type=event_type, duration_s=60)
    return {"message": f"{event_type} event triggered for 60s"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI server at http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)