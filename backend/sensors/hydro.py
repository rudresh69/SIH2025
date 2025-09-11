"""
hydro.py
A realistic hydrological data generator for simulating the effects of rainfall
infiltration on soil moisture and pore water pressure.

This module simulates readings from two common hydrological sensors:
1.  Soil Moisture Sensor (measures volumetric water content)
2.  Piezometer (measures pore water pressure)

Key Features:
-   **Realistic Response Model:** Simulates the lag, peak, and recession (drainage)
    curve of a hydrological event instead of an instantaneous change.
-   **Differentiated Physics:** Models the different response times and characteristics
    of shallow moisture sensors versus deeper piezometers.
-   **Advanced Baseline:** The baseline includes seasonal and diurnal (daily) cycles,
    plus natural low-frequency noise.
-   **Dynamic Event Scheduling:** Can autonomously schedule random "rainfall" events
    based on a configurable rate.
-   **State Exposure:** The `hydro_state` dictionary is exposed for external
    modules to inspect the simulation's ground truth.
"""

import math
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any

import numpy as np

# ----------------- CONFIGURATION -----------------
FS: int = 10  # Sampling frequency in Hz
EVENT_RATE_PER_DAY: float = 0.5  # Average number of rainfall events per day
MIN_COOLDOWN_HOURS: int = 12  # Minimum hours between events
EVENT_MIN_DURATION_S: int = 60 * 10  # 10 minutes
EVENT_MAX_DURATION_S: int = 60 * 120  # 120 minutes
EVENT_MIN_INTENSITY: float = 5.0  # Min intensity, affects saturation rate
EVENT_MAX_INTENSITY: float = 25.0  # Max intensity
SEED: int = 1337

# Initialize random seeds
random.seed(SEED)
np.random.seed(SEED)

# ----------------- SIMULATION STATE -----------------
hydro_state: Dict[str, Any] = {
    "t": 0,  # Global time tick counter
    "event": None,  # Holds active rainfall event data
    "soil_saturation": 0.0,  # The core state variable representing water content. Max ~100.
    "drainage_rate": 0.999,  # Multiplier for saturation decay per tick
    "last_event_end_time": None,
    "scheduled_next_event_time": None,
    "sampling_interval_s": 1.0 / FS
}


# ----------------- UTILITY FUNCTIONS -----------------
def now() -> datetime:
    """Returns the current UTC time."""
    return datetime.utcnow()


def pink_noise(n: int, exponent: float = 1.0) -> np.ndarray:
    """Generates pink noise (1/f noise) of a given length."""
    if n <= 0:
        return np.array([])
    white = np.random.randn(n)
    f = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, d=1.0 / FS)
    freqs[0] = 1e-6
    f_pink = f / (freqs**(exponent / 2.0))
    pink = np.fft.irfft(f_pink, n=n)
    if np.std(pink) == 0:
        return pink
    return (pink - np.mean(pink)) / (np.std(pink) + 1e-9)


# ----------------- CORE EVENT LOGIC -----------------
def _schedule_next_event() -> None:
    """Schedules the next random rainfall event."""
    if EVENT_RATE_PER_DAY <= 0:
        return
    rate_per_s = EVENT_RATE_PER_DAY / (24 * 3600)
    inter_arrival_s = np.random.exponential(1.0 / rate_per_s)
    hydro_state["scheduled_next_event_time"] = now() + timedelta(seconds=inter_arrival_s)


def _maybe_start_scheduled_event() -> None:
    """Checks if a scheduled event should start and initiates it."""
    if hydro_state["event"]:
        return

    if hydro_state["scheduled_next_event_time"] and now() >= hydro_state["scheduled_next_event_time"]:
        if hydro_state["last_event_end_time"]:
            elapsed_hours = (now() - hydro_state["last_event_end_time"]).total_seconds() / 3600
            if elapsed_hours < MIN_COOLDOWN_HOURS:
                return

        duration_s = random.uniform(EVENT_MIN_DURATION_S, EVENT_MAX_DURATION_S)
        intensity = random.uniform(EVENT_MIN_INTENSITY, EVENT_MAX_INTENSITY)
        trigger_event(duration_s=duration_s, intensity=intensity)
        hydro_state["scheduled_next_event_time"] = None


# ----------------- PUBLIC API -----------------
def trigger_event(duration_s: float, intensity: float) -> None:
    """
    Manually triggers a hydrological event (e.g., rainfall).

    Args:
        duration_s (float): The duration of the event in seconds.
        intensity (float): A value representing rainfall intensity, which
                           determines how quickly the soil saturates.
    """
    hydro_state["event"] = {
        "remaining_ticks": int(duration_s * FS),
        "intensity": intensity
    }


def step() -> None:
    """Advances the simulation by one time step."""
    hydro_state['t'] += 1

    # 1. Handle event scheduling
    if hydro_state["scheduled_next_event_time"] is None and EVENT_RATE_PER_DAY > 0:
        _schedule_next_event()
    _maybe_start_scheduled_event()

    # 2. Update soil saturation based on active event
    if hydro_state.get("event"):
        event = hydro_state["event"]
        event["remaining_ticks"] -= 1

        # Increase saturation based on intensity
        saturation_increase = (event["intensity"] / 1000.0) * (1 - hydro_state["soil_saturation"] / 110.0)
        hydro_state["soil_saturation"] += max(0, saturation_increase)

        if event["remaining_ticks"] <= 0:
            hydro_state["event"] = None
            hydro_state["last_event_end_time"] = now()

    # 3. Apply natural drainage (recession)
    hydro_state["soil_saturation"] *= hydro_state["drainage_rate"]
    hydro_state["soil_saturation"] = max(0, hydro_state["soil_saturation"])


def get_readings() -> Dict[str, Any]:
    """
    Advances the simulation one step and returns the new sensor readings.

    Returns:
        Dict[str, Any]: A dictionary containing 'moisture_sensor', 'piezometer',
                        and a binary 'label'.
    """
    step()
    t = hydro_state["t"]
    saturation = hydro_state["soil_saturation"]

    # 1. Calculate baselines with seasonal and diurnal cycles
    seasonal_cycle = 5 * math.sin(2 * math.pi * t / (3600 * 24 * 30 * FS))  # 30-day cycle
    diurnal_cycle = 2 * math.sin(2 * math.pi * t / (3600 * 24 * FS))  # 24-hour cycle
    base_noise = pink_noise(1)[0] * 0.5

    moisture_baseline = 25 + seasonal_cycle - diurnal_cycle + base_noise
    piezometer_baseline = 5 + (seasonal_cycle * 0.4) + (base_noise * 0.3)

    # 2. Calculate sensor values based on soil saturation
    # Moisture sensor responds directly to saturation
    moisture_effect = saturation * 0.7
    moisture = moisture_baseline + moisture_effect

    # Piezometer responds non-linearly, kicking in at higher saturation
    pressure_effect = (saturation**1.5) / 20.0
    piezometer = piezometer_baseline + pressure_effect

    # 3. Final clipping and formatting
    label = 1 if is_event_active() else 0

    return {
        "moisture_sensor": round(float(np.clip(moisture, 0, 100)), 4),
        "piezometer": round(float(np.clip(piezometer, 0, 500)), 4),
        "label": label
    }


def is_event_active() -> bool:
    """
    Returns True if an event is active or if soil saturation is significantly
    above normal levels, indicating a risk period.
    """
    return bool(hydro_state.get("event")) or hydro_state["soil_saturation"] > 15.0


# ----------------- EXECUTION EXAMPLE -----------------
if __name__ == "__main__":
    print("Starting hydro simulation. Press Ctrl+C to exit.")
    print("Moisture (%) | Piezometer (kPa) | Status")
    print("-" * 50)

    # Example of manually triggering a large event at the start
    # trigger_event(duration_s=3600, intensity=20.0)

    while True:
        try:
            readings = get_readings()
            moist_val = readings['moisture_sensor']
            piezo_val = readings['piezometer']
            active_marker = " * EVENT ACTIVE * " if readings['label'] == 1 else ""

            # Simple text visualization
            moist_bar = '#' * int(moist_val / 2)
            piezo_bar = 'x' * int(piezo_val / 2)

            print(
                f"{moist_val:7.2f}% | {piezo_val:13.2f} kPa | {active_marker}"
            )

            time.sleep(hydro_state["sampling_interval_s"])
        except KeyboardInterrupt:
            print("\nSimulation stopped.")
            break
