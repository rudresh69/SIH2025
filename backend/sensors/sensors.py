"""
sensors.py
Unified sensor simulator for the live rockfall monitoring dashboard.
This file contains all logic for a realistic, interactive simulation with
phased events (early warning -> main event). It is designed to be a
drop-in replacement for the live demo.
"""

import time
import numpy as np
from datetime import datetime

# ==============================================================================
# SECTION 1: INDIVIDUAL SENSOR GROUP SIMULATION LOGIC
# ==============================================================================

# ----------------- Seismic Sensor Simulation -----------------
# (No changes needed here, baselines are already centered around 0)
seismic_state = {"active": False, "ticks_left": 0, "magnitude": 1.0, "is_precursor": False}

def trigger_seismic(magnitude: float, duration_s: int, precursor: bool):
    seismic_state.update({"active": True, "ticks_left": duration_s, "magnitude": magnitude, "is_precursor": precursor})

def get_seismic_readings():
    if not seismic_state["active"]:
        return {"accelerometer": np.random.normal(0, 0.05), "geophone": np.random.normal(0, 0.1), "seismometer": np.random.normal(0, 0.08), "label": 0}

    seismic_state["ticks_left"] -= 1
    if seismic_state["ticks_left"] <= 0:
        seismic_state["active"] = False

    if seismic_state["is_precursor"]:
        base_acc = np.sin(time.time() * 2) * seismic_state["magnitude"] * 0.5
        base_geo = np.sin(time.time() * 1.5) * seismic_state["magnitude"] * 1.0
        base_sei = np.sin(time.time() * 2.5) * seismic_state["magnitude"] * 0.8
    else:
        base_acc = np.random.normal(0, 1.5 * seismic_state["magnitude"])
        base_geo = np.random.normal(0, 2.5 * seismic_state["magnitude"])
        base_sei = np.random.normal(0, 2.0 * seismic_state["magnitude"])

    return {"accelerometer": base_acc, "geophone": base_geo, "seismometer": base_sei, "label": 1}


# ----------------- Displacement Sensor Simulation -----------------
# --- UPDATED: Added comments for units to make values feel more real ---
displacement_baselines = {
    "crack_sensor": 0.1,  # in mm
    "inclinometer": 0.0,  # in degrees
    "extensometer": 0.2   # in mm
}
current_displacement_values = displacement_baselines.copy()
displacement_state = {"active": False, "ticks_left": 0, "total_duration": 1, "start_values": {}, "target_values": {}}


def trigger_displacement(total_displacement_mm: float, duration_s: int):
    global current_displacement_values
    current_displacement_values = displacement_baselines.copy() # Reset on new trigger
    displacement_state.update({
        "active": True, "ticks_left": duration_s, "total_duration": duration_s,
        "start_values": current_displacement_values.copy(),
        "target_values": {
            "crack_sensor": current_displacement_values["crack_sensor"] + total_displacement_mm,
            "inclinometer": current_displacement_values["inclinometer"] + (total_displacement_mm * 0.2),
            "extensometer": current_displacement_values["extensometer"] + (total_displacement_mm * 0.5)
        }
    })

def get_displacement_readings():
    global current_displacement_values
    if not displacement_state["active"]:
        current_displacement_values["crack_sensor"] += np.random.normal(0, 0.001)
        return {**current_displacement_values, "label": 0}

    displacement_state["ticks_left"] -= 1
    if displacement_state["ticks_left"] < 0:
        displacement_state["active"] = False
        current_displacement_values = displacement_baselines.copy() # Reset after event
        return {**current_displacement_values, "label": 0}

    progress = 1.0 - (displacement_state["ticks_left"] / displacement_state["total_duration"])
    for sensor in current_displacement_values:
        start = displacement_state["start_values"][sensor]
        target = displacement_state["target_values"][sensor]
        current_displacement_values[sensor] = start + (target - start) * progress

    return {
        "crack_sensor": current_displacement_values["crack_sensor"] + np.random.normal(0, 0.02),
        "inclinometer": current_displacement_values["inclinometer"] + np.random.normal(0, 0.01),
        "extensometer": current_displacement_values["extensometer"] + np.random.normal(0, 0.03),
        "label": 1
    }

# ----------------- Hydro Sensor Simulation -----------------
hydro_state = {"active": False, "ticks_left": 0, "intensity": 0.0}

def trigger_hydro(duration_s: int, intensity: float):
    hydro_state.update({"active": True, "ticks_left": duration_s, "intensity": intensity})

def get_hydro_readings():
    # --- UPDATED: More realistic baseline values ---
    baseline_moisture = 30.0  # in %
    baseline_piezometer = 15.0 # in kPa

    if not hydro_state["active"]:
        return {"moisture_sensor": baseline_moisture + np.random.normal(0, 0.5), "piezometer": baseline_piezometer + np.random.normal(0, 2), "label": 0}

    hydro_state["ticks_left"] -= 1
    if hydro_state["ticks_left"] <= 0:
        hydro_state["active"] = False

    # --- UPDATED: More significant increase during rainfall event ---
    moisture_increase = (hydro_state["intensity"] / 25.0) * 30
    piezo_increase = (hydro_state["intensity"] / 25.0) * 20
    return {"moisture_sensor": baseline_moisture + moisture_increase, "piezometer": baseline_piezometer + piezo_increase, "label": 1}

# ----------------- Environmental Sensor Simulation -----------------
def get_environmental_readings():
    # --- UPDATED: More realistic ambient temperature and humidity for the location ---
    # Added a slow sine wave to temperature to simulate a subtle day/night cycle
    day_cycle_effect = np.sin(time.time() / 300) * 2 # Slow cycle over ~50 minutes
    
    return {
        "rain_sensor_mmhr": 0.0,
        "temperature_celsius": 28.0 + day_cycle_effect + np.random.normal(0, 0.1),
        "humidity_percent": 65.0 - (day_cycle_effect * 5) + np.random.normal(0, 0.5), # Humidity is often inverse to temp
    }

# ==============================================================================
# SECTION 2: GLOBAL ORCHESTRATOR
# (This section remains unchanged)
# ==============================================================================
global_sensor_state = {
    "event_active": False, "event_type": None, "phase": None,
    "ticks_remaining": 0, "phase_transition_tick": 0
}

def trigger_all(event_type: str = "rockfall", duration_s: int = 60) -> None:
    print(f"\n--- TRIGGERING GLOBAL EVENT: {event_type.upper()} ({duration_s}s) ---")
    total_ticks = duration_s * 20
    early_phase_ticks = int(total_ticks * 0.66)
    global_sensor_state.update({
        "event_active": True, "event_type": event_type, "phase": "early_warning",
        "ticks_remaining": total_ticks, "phase_transition_tick": total_ticks - early_phase_ticks
    })
    if event_type == "rockfall":
        trigger_seismic(magnitude=1.0, duration_s=early_phase_ticks, precursor=True)
        trigger_displacement(total_displacement_mm=0.5, duration_s=early_phase_ticks)
    elif event_type == "rainfall":
        trigger_hydro(duration_s=total_ticks, intensity=25.0)
        trigger_displacement(total_displacement_mm=0.2, duration_s=total_ticks)
    elif event_type == "landslide":
        trigger_seismic(magnitude=1.5, duration_s=early_phase_ticks, precursor=True)
        trigger_hydro(duration_s=total_ticks, intensity=15.0)
        trigger_displacement(total_displacement_mm=1.0, duration_s=early_phase_ticks)

def get_all_readings() -> dict:
    if global_sensor_state["event_active"]:
        global_sensor_state["ticks_remaining"] -= 1
        if global_sensor_state["phase"] == "early_warning" and global_sensor_state["ticks_remaining"] <= global_sensor_state["phase_transition_tick"]:
            global_sensor_state["phase"] = "main_event"
            if global_sensor_state["event_type"] == "rockfall":
                trigger_seismic(magnitude=3.0, duration_s=global_sensor_state["ticks_remaining"], precursor=False)
                trigger_displacement(total_displacement_mm=2.5, duration_s=global_sensor_state["ticks_remaining"])
            elif global_sensor_state["event_type"] == "landslide":
                trigger_seismic(magnitude=3.5, duration_s=global_sensor_state["ticks_remaining"], precursor=False)
                trigger_displacement(total_displacement_mm=10.0, duration_s=global_sensor_state["ticks_remaining"])
        if global_sensor_state["ticks_remaining"] <= 0:
            global_sensor_state.update({"event_active": False, "event_type": None, "phase": None})
            
    seismic_data = get_seismic_readings()
    hydro_data = get_hydro_readings()
    displacement_data = get_displacement_readings()
    env_data = get_environmental_readings()
    
    master_label = 1 if any([seismic_data["label"], hydro_data["label"], displacement_data["label"]]) else 0
    
    all_data = {
        "timestamp": datetime.utcnow().isoformat(),
        **seismic_data,
        **hydro_data,
        **displacement_data,
        **env_data,
        "label": master_label,
        "event_active": global_sensor_state["event_active"],
        "event_phase": global_sensor_state["phase"],
    }
    return all_data