"""
displacement.py
A realistic displacement data generator for simulating ground and structural movement.

This module simulates readings from three common displacement sensors:
1.  Crack Sensor (measures the width of a crack in mm)
2.  Inclinometer (measures tilt in degrees)
3.  Extensometer (measures displacement between two points in mm)

Key Features:
-   **Permanent Deformation:** Events cause lasting shifts in the sensor baselines,
    simulating real-world cracks and tilts that do not self-correct.
-   **Realistic Event Profile:** Movement is modeled as a non-linear process,
    simulating creep and acceleration rather than an instantaneous jump.
-   **Advanced Baseline Drift:** The baseline includes seasonal and diurnal (daily)
    thermal cycles, plus a slow, random drift.
-   **Dynamic Event Scheduling:** Can autonomously schedule rare, random displacement
    events over long time scales.
-   **State Exposure:** The `disp_state` dictionary is exposed for external modules
    to inspect the ground truth of the simulation.
"""

import math
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any

import numpy as np

# ----------------- CONFIGURATION -----------------
FS: int = 2  # Sampling frequency in Hz. Displacement is slow.
EVENT_RATE_PER_MONTH: float = 0.5  # Average number of displacement events per month
MIN_COOLDOWN_DAYS: int = 20
EVENT_MIN_DURATION_S: int = 60 * 60 * 1  # 1 hour
EVENT_MAX_DURATION_S: int = 60 * 60 * 24 * 2  # 2 days
EVENT_MIN_MAGNITUDE: float = 0.5  # Affects total displacement (e.g., in mm)
EVENT_MAX_MAGNITUDE: float = 5.0
SEED: int = 2077

# Initialize random seeds
random.seed(SEED)
np.random.seed(SEED)

# ----------------- SIMULATION STATE -----------------
disp_state: Dict[str, Any] = {
    "t": 0,
    "event": None,  # Holds active movement event data
    # --- Permanent State Variables ---
    "crack_offset_mm": 0.1,
    "tilt_offset_deg": 0.05,
    "extensometer_offset_mm": 0.2,
    # ---
    "last_event_end_time": None,
    "scheduled_next_event_time": None,
    "sampling_interval_s": 1.0 / FS
}


# ----------------- UTILITY FUNCTIONS -----------------
def now() -> datetime:
    """Returns the current UTC time."""
    return datetime.utcnow()


# ----------------- CORE EVENT LOGIC -----------------
def _schedule_next_event() -> None:
    """Schedules the next random displacement event."""
    if EVENT_RATE_PER_MONTH <= 0:
        return
    rate_per_s = EVENT_RATE_PER_MONTH / (30 * 24 * 3600)
    inter_arrival_s = np.random.exponential(1.0 / rate_per_s)
    disp_state["scheduled_next_event_time"] = now() + timedelta(seconds=inter_arrival_s)


def _maybe_start_scheduled_event() -> None:
    """Checks if a scheduled event should start and initiates it."""
    if disp_state["event"]:
        return

    if disp_state["scheduled_next_event_time"] and now() >= disp_state["scheduled_next_event_time"]:
        if disp_state["last_event_end_time"]:
            elapsed_days = (now() - disp_state["last_event_end_time"]).total_seconds() / (3600 * 24)
            if elapsed_days < MIN_COOLDOWN_DAYS:
                return

        duration_s = random.uniform(EVENT_MIN_DURATION_S, EVENT_MAX_DURATION_S)
        magnitude = random.uniform(EVENT_MIN_MAGNITUDE, EVENT_MAX_MAGNITUDE)
        trigger_event(total_displacement_mm=magnitude, duration_s=duration_s)
        disp_state["scheduled_next_event_time"] = None


# ----------------- PUBLIC API -----------------
def trigger_event(total_displacement_mm: float, duration_s: float) -> None:
    """
    Manually triggers a displacement event.

    Args:
        total_displacement_mm (float): The total amount of movement the event will cause.
        duration_s (float): The duration over which the movement occurs.
    """
    total_ticks = int(duration_s * FS)
    disp_state["event"] = {
        "ticks_remaining": total_ticks,
        "total_ticks": total_ticks,
        "total_displacement": total_displacement_mm,
        "last_displacement_total": 0.0,
    }


def step() -> None:
    """Advances the simulation by one time step."""
    disp_state['t'] += 1

    # 1. Handle event scheduling
    if disp_state["scheduled_next_event_time"] is None and EVENT_RATE_PER_MONTH > 0:
        _schedule_next_event()
    _maybe_start_scheduled_event()

    # 2. Process active event and update permanent offsets
    if disp_state.get("event"):
        event = disp_state["event"]
        event["ticks_remaining"] -= 1

        # Calculate current progress through the event (0.0 to 1.0)
        progress = (event["total_ticks"] - event["ticks_remaining"]) / event["total_ticks"]

        # Use tanh to create an S-curve for displacement over time
        # This simulates slow start -> acceleration -> slow end
        current_total_disp = event["total_displacement"] * (0.5 * (np.tanh(6 * progress - 3) + 1))
        
        # The displacement for THIS step is the difference from the last step
        displacement_this_step = current_total_disp - event["last_displacement_total"]
        event["last_displacement_total"] = current_total_disp

        # Apply this step's displacement to the permanent offsets with different sensitivities
        disp_state["crack_offset_mm"] += displacement_this_step * 0.8  # Cracks might show most movement
        disp_state["tilt_offset_deg"] += displacement_this_step * 0.2  # Tilt is less sensitive
        disp_state["extensometer_offset_mm"] += displacement_this_step * 1.0 # Extensometer measures directly

        if event["ticks_remaining"] <= 0:
            disp_state["event"] = None
            disp_state["last_event_end_time"] = now()


def get_readings() -> Dict[str, Any]:
    """
    Advances the simulation one step and returns the new sensor readings.

    Returns:
        Dict[str, Any]: A dictionary containing 'crack_sensor', 'inclinometer',
                        'extensometer' readings, and a binary 'label'.
    """
    step()
    t = disp_state["t"]

    # 1. Calculate baseline drift from thermal cycles
    # Very slow cycle for seasonal temperature changes
    seasonal_drift = 0.02 * math.sin(2 * math.pi * t / (3600 * 24 * 365 * FS))
    # Daily cycle for day/night temperature changes
    diurnal_drift = 0.03 * math.sin(2 * math.pi * t / (3600 * 24 * FS))
    total_drift = seasonal_drift + diurnal_drift

    # 2. Get permanent offsets and add drift and noise
    crack = disp_state["crack_offset_mm"] + total_drift * 0.5 + random.gauss(0, 0.005)
    tilt = disp_state["tilt_offset_deg"] + total_drift * 0.2 + random.gauss(0, 0.002)
    extensometer = disp_state["extensometer_offset_mm"] + total_drift * 1.0 + random.gauss(0, 0.005)

    # 3. Final formatting
    label = 1 if is_event_active() else 0

    return {
        "crack_sensor": round(float(max(0, crack)), 4),
        "inclinometer": round(float(max(0, tilt)), 4),
        "extensometer": round(float(max(0, extensometer)), 4),
        "label": label
    }


def is_event_active() -> bool:
    """
    Returns True if an event is actively causing displacement.
    Note: The effects (changed offsets) of an event are permanent.
    """
    return bool(disp_state.get("event"))


# ----------------- EXECUTION EXAMPLE -----------------
if __name__ == "__main__":
    print("Starting displacement simulation. Press Ctrl+C to exit.")
    print("Crack (mm) | Tilt (deg) | Extensometer (mm) | Status")
    print("-" * 70)

    # Example of manually triggering a slow event at the start
    trigger_event(total_displacement_mm=2.5, duration_s=60) # A 1-minute event for demo

    while True:
        try:
            readings = get_readings()
            crack_val = readings['crack_sensor']
            tilt_val = readings['inclinometer']
            ext_val = readings['extensometer']
            active_marker = " * MOVING * " if readings['label'] == 1 else ""

            print(
                f"{crack_val:10.4f} | {tilt_val:10.4f} | {ext_val:17.4f} | {active_marker}"
            )

            time.sleep(disp_state["sampling_interval_s"])
        except KeyboardInterrupt:
            print("\nSimulation stopped.")
            break
