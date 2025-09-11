"""
environmental.py
A realistic environmental data generator for simulating weather conditions.

This module simulates readings from common environmental sensors:   
1.  Rain Sensor (measures rainfall in mm/hr)
2.  Temperature Sensor (measures air temperature in Celsius)
3.  Humidity Sensor (measures relative humidity in %)

Key Features:
-   **Stateful Events:** Rain events have duration and intensity, creating realistic storms.
-   **Realistic Baselines:** Temperature and humidity follow seasonal and diurnal cycles.
-   **State Exposure:** The `env_state` dictionary is exposed for external modules
    to inspect the ground truth of the simulation.
"""

import math
import random
import time
from typing import Dict, Any

# ----------------- CONFIGURATION -----------------
FS: int = 2  # Sampling frequency in Hz
RAIN_EVENT_PROB_PER_STEP: float = 0.0001  # Chance of a rainstorm starting
SEED: int = 42

random.seed(SEED)

# ----------------- SIMULATION STATE -----------------
env_state: Dict[str, Any] = {
    "t": 0,
    "rain_event": None,  # Holds active rain event data
    "sampling_interval_s": 1.0 / FS
}


# ----------------- CORE LOGIC -----------------
def step() -> None:
    """Advances the simulation by one time step."""
    env_state['t'] += 1

    # Manage rain events
    if env_state.get("rain_event"):
        event = env_state["rain_event"]
        event["ticks_remaining"] -= 1
        if event["ticks_remaining"] <= 0:
            env_state["rain_event"] = None
    elif random.random() < RAIN_EVENT_PROB_PER_STEP:
        # Start a new rain event
        env_state["rain_event"] = {
            "ticks_remaining": int(random.uniform(3600, 3600 * 8) * FS),  # 1-8 hours
            "intensity": random.uniform(5, 50)  # mm/hr
        }


def get_readings() -> Dict[str, Any]:
    """
    Advances the simulation one step and returns the new sensor readings.

    Returns:
        A dictionary containing all environmental sensor readings.
    """
    step()
    t = env_state["t"]

    # 1. Rain sensor reading
    rain = 0.0
    if env_state["rain_event"]:
        rain = env_state["rain_event"]["intensity"] + random.uniform(-1, 1)
    rain += random.uniform(0, 0.2)  # Background drizzle/noise

    # 2. Temperature and Humidity with seasonal and diurnal cycles
    seasonal_temp_mod = 8 * math.sin(2 * math.pi * t / (3600 * 24 * 365 * FS))
    diurnal_temp_mod = 5 * math.sin(2 * math.pi * t / (3600 * 24 * FS))
    base_temp = 15  # Average temperature
    temperature = base_temp + seasonal_temp_mod + diurnal_temp_mod + random.gauss(0, 0.2)

    # Humidity is often inversely related to temperature
    base_humidity = 60
    humidity = base_humidity - (diurnal_temp_mod * 4) + random.gauss(0, 2)
    if env_state["rain_event"]:
        humidity += 20 # Rain increases humidity

    return {
        "rain_sensor_mmhr": round(float(max(0, rain)), 2),
        "temperature_celsius": round(float(temperature), 2),
        "humidity_percent": round(float(max(0, min(100, humidity))), 2)
    }


# ----------------- EXECUTION EXAMPLE -----------------
if __name__ == "__main__":
    print("Starting environmental simulation. Press Ctrl+C to exit.")
    print("Rain (mm/hr) | Temp (°C)  | Humidity (%)")
    print("-" * 50)

    while True:
        try:
            readings = get_readings()
            rain_val = readings['rain_sensor_mmhr']
            temp_val = readings['temperature_celsius']
            hum_val = readings['humidity_percent']
            
            is_raining = "RAINING" if rain_val > 1.0 else ""

            print(
                f"{rain_val:12.2f} | {temp_val:10.2f} | {hum_val:12.2f} | {is_raining}"
            )

            time.sleep(env_state["sampling_interval_s"])
        except KeyboardInterrupt:
            print("\nSimulation stopped.")
            break
