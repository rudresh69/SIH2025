"""
sensors.py
Simulated sensor aggregator for the alert system.
Generates random sensor data and triggers emergency or warning events.
"""

import random
from datetime import datetime

# Global state to track current alert
current_alert = {
    "status": "Safe",   # "Safe", "Warning", "Emergency"
    "place": "Main Road",
    "sound": False      # True when emergency sound should play
}

# ----------------- TRIGGER EVENTS -----------------
def trigger_event(event_type: str):
    """
    Trigger a simulated event:
    - 'safe': normal state
    - 'warning': caution state
    - 'emergency': critical state
    """
    global current_alert
    if event_type.lower() == "safe":
        current_alert = {
            "status": "Safe",
            "place": current_alert.get("place", "Unknown"),
            "sound": False
        }
    elif event_type.lower() == "warning":
        current_alert = {
            "status": "Warning",
            "place": current_alert.get("place", "Unknown"),
            "sound": False
        }
    elif event_type.lower() == "emergency":
        current_alert = {
            "status": "Emergency",
            "place": current_alert.get("place", "Unknown"),
            "sound": True
        }

# ----------------- GET SENSOR READINGS -----------------
def get_readings():
    """
    Returns simulated sensor readings including the current alert status.
    """
    # Simulate some sensor data
    data = {
        "temperature_celsius": round(random.uniform(20.0, 40.0), 1),
        "humidity_percent": round(random.uniform(30.0, 80.0), 1),
        "vibration": round(random.uniform(0.0, 5.0), 2),
        "traffic_density": random.randint(0, 100),
        "timestamp": datetime.now().isoformat(),
        "status": current_alert["status"],
        "place": current_alert["place"],
        "sound": current_alert["sound"]
    }
    return data

# ----------------- DEMO -----------------
if __name__ == "__main__":
    import time
    print("Starting sensor simulation...")
    while True:
        readings = get_readings()
        print(readings)
        time.sleep(1)
