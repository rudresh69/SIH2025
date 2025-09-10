from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time

# Import unified sensor manager
import sensors

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Dummy ML Model (replace later) ===
def predict_risk(features: dict) -> str:
    """
    Placeholder ML model for demo.
    Takes sensor readings and returns a risk level.
    """
    vibration = max(
        features["accelerometer"],
        features["geophone"],
        features["seismometer"]
    )
    crack = features["crack_sensor"]
    moisture = features["moisture_sensor"]
    rain = features["rain_sensor"]

    # Dummy thresholds (to be replaced with real model prediction)
    if (vibration > 1.5 or crack > 3) and (rain > 50 or moisture > 60):
        return "HIGH"
    elif vibration > 0.5 or crack > 1:
        return "MEDIUM"
    else:
        return "LOW"

# === Endpoints ===

@app.get("/sensors")
def get_all_sensors():
    """
    Get a combined frame of all sensor readings.
    """
    readings = sensors.get_all_readings()
    readings["timestamp"] = time.time()
    return readings

@app.post("/trigger/{event_type}")
def trigger_event(event_type: str, duration: int = 20):
    """
    Manually trigger an event across all sensors.
    event_type: "rockfall", "rainfall", "landslide"
    """
    sensors.trigger_all(event_type, duration_s=duration)
    return {"status": "triggered", "event": event_type, "duration_s": duration}

@app.get("/risk-level")
def get_risk_level():
    """
    Get risk level from ML model (currently dummy).
    """
    readings = sensors.get_all_readings()
    risk = predict_risk(readings)
    readings["risk_level"] = risk
    readings["timestamp"] = time.time()
    return readings
