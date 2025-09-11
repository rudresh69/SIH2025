"""
main.py
This script creates a FastAPI application to serve live sensor data and
provide real-time rockfall risk predictions using the trained 1D CNN model.
"""

import os
import torch
import uvicorn
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from collections import deque
from sklearn.preprocessing import StandardScaler
import sys

# --- PATH SETUP ---
# Add the backend directory to the system path to ensure correct module imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# --- IMPORT LOCAL MODULES ---
from sensors import sensors
from ml_model.models import RockfallCNN # Use the updated RockfallCNN model

# --- CONFIGURATION & GLOBAL STATE ---
WINDOW_SIZE = 50  # Must match the WINDOW_SIZE used during training
NUM_FEATURES = 11 # The total number of sensor features
# This buffer will store the last WINDOW_SIZE readings to create a prediction window
data_buffer = deque(maxlen=WINDOW_SIZE)
# This scaler should ideally be loaded from a file saved during training
# For this example, we create a new one.
scaler = StandardScaler()

# --- DEVICE SETUP ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- MODEL LOADING ---
MODEL_PATH = os.path.join(BASE_DIR, "ml_model", "best_cnn_model.pth")
# Correctly instantiate the model with the number of features
model = RockfallCNN(num_features=NUM_FEATURES, num_classes=2)

if os.path.exists(MODEL_PATH):
    print(f"✅ Loading model from {MODEL_PATH}")
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.to(device)
    model.eval() # Set the model to evaluation mode
else:
    print(f"⚠️ Model file not found at {MODEL_PATH}. API will run but predictions will fail.")
    model = None # Set model to None if not found

# --- FASTAPI SETUP ---
app = FastAPI(
    title="Rockfall Prediction API",
    description="Provides live sensor data and predicts rockfall risk using a 1D CNN."
)

# --- PYDANTIC MODELS (for request/response validation) ---
class SensorData(BaseModel):
    accelerometer: float
    geophone: float
    seismometer: float
    moisture_sensor: float
    piezometer: float
    crack_sensor: float
    inclinometer: float
    extensometer: float
    rain_sensor_mmhr: float
    temperature_celsius: float
    humidity_percent: float
    label: int
    timestamp: str

class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    is_buffer_full: bool
    message: str

# --- API ROUTES ---
@app.get("/sensors/live", response_model=SensorData)
def get_live_sensors():
    """
    Returns a single frame of the most recent live readings from all sensors.
    """
    readings = sensors.get_all_readings()
    return readings

@app.post("/predict/live", response_model=PredictionResponse)
def predict_from_live_data():
    """
    Fetches a new live sensor reading, updates the data buffer,
    and returns a risk prediction if the buffer is full.
    """
    if not model:
        raise HTTPException(status_code=503, detail="Model is not loaded. Cannot make predictions.")

    # 1. Get the latest sensor data
    live_readings = sensors.get_all_readings()
    
    # 2. Extract feature values in the correct order
    features = [
        live_readings[key] for key in [
            "accelerometer", "geophone", "seismometer", "moisture_sensor", "piezometer",
            "crack_sensor", "inclinometer", "extensometer", "rain_sensor_mmhr",
            "temperature_celsius", "humidity_percent"
        ]
    ]
    data_buffer.append(features)

    # 3. Check if the buffer is full
    if len(data_buffer) < WINDOW_SIZE:
        return {
            "prediction": "Not Available",
            "confidence": 0.0,
            "is_buffer_full": False,
            "message": f"Collecting data... {len(data_buffer)}/{WINDOW_SIZE} readings in buffer."
        }

    # 4. If buffer is full, prepare the data for the model
    # Convert buffer to a numpy array for scaling
    window_data = np.array(data_buffer)
    
    # Scale the data. NOTE: In production, fit the scaler on training data ONLY.
    # Here, we fit on the current window for demonstration purposes.
    scaled_window = scaler.fit_transform(window_data)
    
    # Convert to a PyTorch tensor and add a batch dimension (1, window_size, num_features)
    input_tensor = torch.tensor(scaled_window, dtype=torch.float32).unsqueeze(0).to(device)

    # 5. Make a prediction
    with torch.no_grad():
        logits = model(input_tensor)
        probabilities = torch.softmax(logits, dim=1)
        confidence, predicted_class_idx = torch.max(probabilities, dim=1)
    
    prediction_label = "Event Detected" if predicted_class_idx.item() == 1 else "Normal"
    
    return {
        "prediction": prediction_label,
        "confidence": round(confidence.item(), 4),
        "is_buffer_full": True,
        "message": "Prediction based on the last 50 readings."
    }

# Add this new endpoint to your main.py
@app.post("/trigger_event/{event_type}")
def trigger_event_now(event_type: str):
    """
    Manually triggers a global sensor event for demonstration.
    Valid event_types: "rockfall", "rainfall", "landslide".
    """
    if event_type not in ["rockfall", "rainfall", "landslide"]:
        raise HTTPException(status_code=400, detail="Invalid event type.")
    
    sensors.trigger_all(event_type=event_type, duration_s=20)
    return {"message": f"'{event_type}' event triggered for 20 seconds."}
    
# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("Starting Rockfall Risk API...")
    print("Navigate to http://127.0.0.1:8000/docs for the API interface.")
    # The `reload=True` is great for development.
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
