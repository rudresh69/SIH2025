# backend/main.py

import os
import torch
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# ----------------- IMPORT SENSOR MODULE -----------------
from .sensors import sensors  # unified sensors.py

# ----------------- IMPORT CNN MODEL -----------------
from .ml_model.cnn_model import CNN1D

# ----------------- DEVICE SETUP -----------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ----------------- MODEL LOADING -----------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), "ml_model", "best_cnn_model.pth")
model = CNN1D()
if os.path.exists(MODEL_PATH):
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.to(device)
    model.eval()
else:
    print(f"⚠️ Model file not found at {MODEL_PATH}. Please check path.")

# ----------------- FASTAPI SETUP -----------------
app = FastAPI(title="Rockfall Risk API")

# ----------------- REQUEST MODEL -----------------
class SensorData(BaseModel):
    accelerometer: float
    geophone: float
    seismometer: float
    crack_sensor: float
    inclinometer: float
    extensometer: float
    moisture_sensor: float
    piezometer: float

# ----------------- ROUTES -----------------
@app.get("/sensors/live")
def get_live_sensors():
    """Return live readings from all sensors."""
    return sensors.get_all_readings()


@app.post("/predict")
def predict_risk(data: SensorData):
    """Predict rockfall risk using CNN model."""
    # Convert input to tensor with shape (1, T, C)
    # Here T=1 (single timestep), C=8 (number of features)
    features = [
        data.accelerometer, data.geophone, data.seismometer,
        data.crack_sensor, data.inclinometer, data.extensometer,
        data.moisture_sensor, data.piezometer
    ]
    x = torch.tensor([features], dtype=torch.float32).unsqueeze(1).to(device)  # (1, 1, 8)
    
    with torch.no_grad():
        pred = model(x).item()  # scalar
    return {"risk_score": pred}

# ----------------- RUN DEMO (OPTIONAL) -----------------
if __name__ == "__main__":
    print("Starting Rockfall Risk API on http://127.0.0.1:8000")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
