import random
import math
import time

# Global state for hydro sensors
hydro_state = {
    "t": 0,
    "event": None  # active water infiltration / rising groundwater event
}

def trigger_event(moisture_increase=30, pressure_increase=25, duration_s=30):
    """Manually trigger a hydro event (e.g., heavy rainfall infiltration)."""
    hydro_state["event"] = {
        "remaining": duration_s * 10,  # simulate at 10Hz
        "moisture_increase": moisture_increase,
        "pressure_increase": pressure_increase
    }

def step_time():
    """Advance time and update event state."""
    hydro_state["t"] += 1
    if hydro_state["event"]:
        hydro_state["event"]["remaining"] -= 1
        if hydro_state["event"]["remaining"] <= 0:
            hydro_state["event"] = None

def moisture_sensor():
    """Soil moisture (%) — rises sharply when water infiltrates."""
    t = hydro_state["t"]
    baseline = 25 + 5 * math.sin(0.001 * t)  # normal fluctuation around 25%

    event_val = 0
    if hydro_state["event"]:
        decay = math.exp(-0.01 * (hydro_state["event"]["remaining"]))
        event_val = hydro_state["event"]["moisture_increase"] * (1 - decay)

    noise = random.gauss(0, 1)
    return round(baseline + event_val + noise, 2)

def piezometer():
    """Pore water pressure (kPa) — rises with groundwater buildup."""
    t = hydro_state["t"]
    baseline = 5 + 2 * math.sin(0.0005 * t)  # normal fluctuation ~5 kPa

    event_val = 0
    if hydro_state["event"]:
        decay = math.exp(-0.015 * (hydro_state["event"]["remaining"]))
        event_val = hydro_state["event"]["pressure_increase"] * (1 - decay)

    noise = random.gauss(0, 0.5)
    return round(baseline + event_val + noise, 2)

def get_readings():
    """Return sensor readings + label (0=normal, 1=hydro risk event)."""
    step_time()
    moist = moisture_sensor()
    press = piezometer()
    label = 1 if hydro_state["event"] else 0
    return {
        "moisture": moist,
        "piezometer": press,
        "label": label
    }

# Test loop
if __name__ == "__main__":
    print("Simulating hydro sensors (Ctrl+C to stop)...")
    while True:
        readings = get_readings()
        print(readings)
        time.sleep(0.1)  # 10Hz
