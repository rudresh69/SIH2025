import random
import math
import time

# Global state for displacement sensors
disp_state = {
    "t": 0,
    "event": None  # crack widening / ground movement event
}

def trigger_event(crack_increase=4, tilt_increase=1.5, extensometer_increase=1.5, duration_s=30):
    """
    Manually trigger a displacement event (e.g., crack widening, slope tilt, ground stretching).
    """
    disp_state["event"] = {
        "remaining": duration_s * 10,  # simulate at 10Hz
        "crack_increase": crack_increase,
        "tilt_increase": tilt_increase,
        "extensometer_increase": extensometer_increase
    }

def step_time():
    """Advance simulation time and reduce event countdown."""
    disp_state["t"] += 1
    if disp_state["event"]:
        disp_state["event"]["remaining"] -= 1
        if disp_state["event"]["remaining"] <= 0:
            disp_state["event"] = None

def crack_sensor():
    """Crack width in mm — stable baseline with sharp increase during event."""
    t = disp_state["t"]
    baseline = 0.05 + 0.02 * math.sin(0.0008 * t)  # ~0.05mm baseline

    event_val = 0
    if disp_state["event"]:
        decay = math.exp(-0.01 * disp_state["event"]["remaining"])
        event_val = disp_state["event"]["crack_increase"] * (1 - decay)

    noise = random.gauss(0, 0.01)
    return round(baseline + event_val + noise, 3)

def inclinometer():
    """Tilt angle in degrees — baseline small drift, rises in event."""
    t = disp_state["t"]
    baseline = 0.1 + 0.05 * math.sin(0.0005 * t)  # ~0.1° baseline

    event_val = 0
    if disp_state["event"]:
        decay = math.exp(-0.012 * disp_state["event"]["remaining"])
        event_val = disp_state["event"]["tilt_increase"] * (1 - decay)

    noise = random.gauss(0, 0.02)
    return round(baseline + event_val + noise, 3)

def extensometer():
    """Ground displacement in mm — baseline tiny movement, rises in event."""
    t = disp_state["t"]
    baseline = 0.05 + 0.02 * math.sin(0.0006 * t)  # ~0.05mm baseline

    event_val = 0
    if disp_state["event"]:
        decay = math.exp(-0.009 * disp_state["event"]["remaining"])
        event_val = disp_state["event"]["extensometer_increase"] * (1 - decay)

    noise = random.gauss(0, 0.01)
    return round(baseline + event_val + noise, 3)

def get_readings():
    """Return sensor readings + label (0=normal, 1=displacement risk event)."""
    step_time()
    crack = crack_sensor()
    tilt = inclinometer()
    ext = extensometer()
    label = 1 if disp_state["event"] else 0
    return {
        "crack_sensor": crack,
        "inclinometer": tilt,
        "extensometer": ext,
        "label": label
    }

# Test loop
if __name__ == "__main__":
    print("Simulating displacement sensors (Ctrl+C to stop)...")
    while True:
        readings = get_readings()
        print(readings)
        time.sleep(0.1)  # 10Hz
