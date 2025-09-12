"""
sensors.py
Unified sensor simulator with a 10-second prediction latency period.
"""

import time
import numpy as np
from datetime import datetime

# ==============================================================================
# SECTION 1: INDIVIDUAL SENSOR GROUP SIMULATION LOGIC
# ==============================================================================

# ----------------- Seismic Sensor Simulation -----------------
seismic_state = {"active": False, "ticks_left": 0, "total_duration": 0, "magnitude": 1.0, "is_precursor": False}

def trigger_seismic(magnitude: float, duration_s: int, precursor: bool):
    seismic_state.update({"active": True, "ticks_left": duration_s, "total_duration": duration_s, "magnitude": magnitude, "is_precursor": precursor})

def get_seismic_readings():
    if not seismic_state["active"]:
        return {"accelerometer": np.random.normal(0, 0.005), "geophone": np.random.normal(0, 0.01), "seismometer": np.random.normal(0, 0.008), "label": 0}

    seismic_state["ticks_left"] -= 1
    if seismic_state["ticks_left"] <= 0:
        seismic_state["active"] = False

    if seismic_state["is_precursor"]:
        latency_s = 10
        time_elapsed_s = seismic_state["total_duration"] - seismic_state["ticks_left"]
        
        # --- FIXED: During latency, send normal noise but with an event label ---
        if time_elapsed_s <= latency_s:
            return {
                "accelerometer": np.random.normal(0, 0.005),
                "geophone": np.random.normal(0, 0.01),
                "seismometer": np.random.normal(0, 0.008),
                "label": 1 # The event is active, but clues haven't started
            }
        
        # After latency, ramp up the precursor signal
        effective_duration = seismic_state["total_duration"] - latency_s
        effective_elapsed = time_elapsed_s - latency_s
        progress = min(effective_elapsed / effective_duration, 1.0)

        base_acc = np.sin(time.time() * 2) * seismic_state["magnitude"] * 0.5 * progress
        base_geo = np.sin(time.time() * 1.5) * seismic_state["magnitude"] * 1.0 * progress
        base_sei = np.sin(time.time() * 2.5) * seismic_state["magnitude"] * 0.8 * progress
    else: # Main event
        base_acc = np.random.normal(0, 1.5 * seismic_state["magnitude"])
        base_geo = np.random.normal(0, 2.5 * seismic_state["magnitude"])
        base_sei = np.random.normal(0, 2.0 * seismic_state["magnitude"])

    return {"accelerometer": base_acc, "geophone": base_geo, "seismometer": base_sei, "label": 1}

# ----------------- Displacement Sensor Simulation -----------------
displacement_baselines = {"crack_sensor": 0.1, "inclinometer": 0.0, "extensometer": 0.2}
current_displacement_values = displacement_baselines.copy()
displacement_state = {"active": False, "ticks_left": 0, "total_duration": 1, "start_values": {}, "target_values": {}}

def trigger_displacement(total_displacement_mm: float, duration_s: int):
    global current_displacement_values
    current_displacement_values = displacement_baselines.copy()
    displacement_state.update({"active": True, "ticks_left": duration_s, "total_duration": duration_s, "start_values": current_displacement_values.copy(), "target_values": {"crack_sensor": current_displacement_values["crack_sensor"] + total_displacement_mm, "inclinometer": current_displacement_values["inclinometer"] + (total_displacement_mm * 0.2), "extensometer": current_displacement_values["extensometer"] + (total_displacement_mm * 0.5)}})

def get_displacement_readings():
    global current_displacement_values
    if not displacement_state["active"]:
        return {**current_displacement_values, "label": 0}

    displacement_state["ticks_left"] -= 1
    if displacement_state["ticks_left"] < 0:
        displacement_state["active"] = False
        current_displacement_values = displacement_baselines.copy()
        return {**current_displacement_values, "label": 0}

    latency_s = 10
    time_elapsed_s = displacement_state["total_duration"] - displacement_state["ticks_left"]

    # --- FIXED: During latency, send normal drifting values but with an event label ---
    if time_elapsed_s <= latency_s:
        current_displacement_values["crack_sensor"] += np.random.normal(0, 0.0001)
        return {**current_displacement_values, "label": 1}

    # After latency, start the slow creep
    effective_duration = displacement_state["total_duration"] - latency_s
    effective_elapsed = time_elapsed_s - latency_s
    progress = min(effective_elapsed / effective_duration, 1.0)
    
    for sensor in current_displacement_values:
        start = displacement_state["start_values"][sensor]
        target = displacement_state["target_values"][sensor]
        current_displacement_values[sensor] = start + (target - start) * progress

    return {"crack_sensor": current_displacement_values["crack_sensor"], "inclinometer": current_displacement_values["inclinometer"], "extensometer": current_displacement_values["extensometer"], "label": 1}

# (The rest of the file - hydro, environmental, and the orchestrator - remains the same)
# ...
hydro_state = {"active": False, "ticks_left": 0, "intensity": 0.0}
def trigger_hydro(duration_s: int, intensity: float): hydro_state.update({"active": True, "ticks_left": duration_s, "intensity": intensity})
def get_hydro_readings():
    baseline_moisture, baseline_piezometer = 0.5, 0.2
    if not hydro_state["active"]: return {"moisture_sensor": baseline_moisture + np.random.normal(0, 0.01), "piezometer": baseline_piezometer + np.random.normal(0, 0.01), "label": 0}
    hydro_state["ticks_left"] -= 1
    if hydro_state["ticks_left"] <= 0: hydro_state["active"] = False
    moisture_increase = (hydro_state["intensity"] / 25.0) * 15
    piezo_increase = (hydro_state["intensity"] / 25.0) * 10
    return {"moisture_sensor": baseline_moisture + moisture_increase, "piezometer": baseline_piezometer + piezo_increase, "label": 1}
def get_environmental_readings(): return {"rain_sensor_mmhr": 0.0, "temperature_celsius": 0.8 + np.random.normal(0, 0.01), "humidity_percent": 1.0 + np.random.normal(0, 0.02)}
global_sensor_state = { "event_active": False, "event_type": None, "phase": None, "ticks_remaining": 0, "phase_transition_tick": 0 }
def trigger_all(event_type: str = "rockfall", duration_s: int = 60) -> None:
    print(f"\n--- TRIGGERING GLOBAL EVENT: {event_type.upper()} ({duration_s}s) ---")
    total_ticks = duration_s * 20
    
    # New timeline:
    # 0-5s: Normal (100 ticks)
    # 5-20s: Warning with clues (300 ticks) 
    # 20-40s: Danger with audio + clues (400 ticks)
    # 40-60s: Actual rockfall (400 ticks)
    
    normal_phase_ticks = 5 * 20  # 5 seconds normal
    warning_phase_ticks = 15 * 20  # 15 seconds warning (5-20s)
    danger_phase_ticks = 20 * 20  # 20 seconds danger (20-40s)
    main_event_ticks = 20 * 20  # 20 seconds main event (40-60s)
    
    global_sensor_state.update({ 
        "event_active": True, 
        "event_type": event_type, 
        "phase": "normal", 
        "ticks_remaining": total_ticks, 
        "normal_phase_tick": total_ticks - normal_phase_ticks,
        "warning_phase_tick": total_ticks - normal_phase_ticks - warning_phase_ticks,
        "danger_phase_tick": total_ticks - normal_phase_ticks - warning_phase_ticks - danger_phase_ticks,
        "main_event_tick": total_ticks - normal_phase_ticks - warning_phase_ticks - danger_phase_ticks - main_event_ticks
    })
    # Don't trigger sensors here - they will be triggered in the phase transitions
    # if event_type == "rockfall":
    #     trigger_seismic(magnitude=1.0, duration_s=early_phase_ticks, precursor=True)
    #     trigger_displacement(total_displacement_mm=0.5, duration_s=early_phase_ticks)
    # elif event_type == "rainfall":
    #     trigger_hydro(duration_s=total_ticks, intensity=25.0)
    #     trigger_displacement(total_displacement_mm=0.2, duration_s=total_ticks)
    # elif event_type == "landslide":
    #     trigger_seismic(magnitude=1.5, duration_s=early_phase_ticks, precursor=True)
    #     trigger_hydro(duration_s=total_ticks, intensity=15.0)
    #     trigger_displacement(total_displacement_mm=1.0, duration_s=early_phase_ticks)
def get_all_readings() -> dict:
    if global_sensor_state["event_active"]:
        global_sensor_state["ticks_remaining"] -= 1
        
        # Phase transitions: normal -> warning -> danger -> main_event
        if global_sensor_state["phase"] == "normal" and global_sensor_state["ticks_remaining"] <= global_sensor_state["normal_phase_tick"]:
            global_sensor_state["phase"] = "warning"
            event_type = global_sensor_state["event_type"]
            print(f"⚠️ WARNING PHASE: Receiving unusual readings - Potential {event_type} detected")
            # Start clue-like sensor values based on event type
            if event_type == "rockfall":
                trigger_seismic(magnitude=0.5, duration_s=global_sensor_state["ticks_remaining"], precursor=True)
                trigger_displacement(total_displacement_mm=0.1, duration_s=global_sensor_state["ticks_remaining"])
            elif event_type == "rainfall":
                trigger_hydro(duration_s=global_sensor_state["ticks_remaining"], intensity=5.0)
                trigger_displacement(total_displacement_mm=0.05, duration_s=global_sensor_state["ticks_remaining"])
            elif event_type == "landslide":
                trigger_seismic(magnitude=0.3, duration_s=global_sensor_state["ticks_remaining"], precursor=True)
                trigger_hydro(duration_s=global_sensor_state["ticks_remaining"], intensity=8.0)
                trigger_displacement(total_displacement_mm=0.2, duration_s=global_sensor_state["ticks_remaining"])
                
        elif global_sensor_state["phase"] == "warning" and global_sensor_state["ticks_remaining"] <= global_sensor_state["warning_phase_tick"]:
            global_sensor_state["phase"] = "danger"
            event_type = global_sensor_state["event_type"]
            print(f"🚨 DANGER PHASE: Evacuate immediately! Audio alert activated!")
            # Continue clue-like values but with audio alert
            if event_type == "rockfall":
                trigger_seismic(magnitude=1.0, duration_s=global_sensor_state["ticks_remaining"], precursor=True)
                trigger_displacement(total_displacement_mm=0.3, duration_s=global_sensor_state["ticks_remaining"])
            elif event_type == "rainfall":
                trigger_hydro(duration_s=global_sensor_state["ticks_remaining"], intensity=15.0)
                trigger_displacement(total_displacement_mm=0.15, duration_s=global_sensor_state["ticks_remaining"])
            elif event_type == "landslide":
                trigger_seismic(magnitude=0.8, duration_s=global_sensor_state["ticks_remaining"], precursor=True)
                trigger_hydro(duration_s=global_sensor_state["ticks_remaining"], intensity=12.0)
                trigger_displacement(total_displacement_mm=0.5, duration_s=global_sensor_state["ticks_remaining"])
                
        elif global_sensor_state["phase"] == "danger" and global_sensor_state["ticks_remaining"] <= global_sensor_state["danger_phase_tick"]:
            global_sensor_state["phase"] = "main_event"
            event_type = global_sensor_state["event_type"]
            print(f"💥 MAIN EVENT: {event_type.title()} in progress! Dramatic sensor values!")
            # Start actual event with dramatic values
            if event_type == "rockfall":
                trigger_seismic(magnitude=3.0, duration_s=global_sensor_state["ticks_remaining"], precursor=False)
                trigger_displacement(total_displacement_mm=2.5, duration_s=global_sensor_state["ticks_remaining"])
            elif event_type == "rainfall":
                trigger_hydro(duration_s=global_sensor_state["ticks_remaining"], intensity=35.0)
                trigger_displacement(total_displacement_mm=0.8, duration_s=global_sensor_state["ticks_remaining"])
            elif event_type == "landslide":
                trigger_seismic(magnitude=3.5, duration_s=global_sensor_state["ticks_remaining"], precursor=False)
                trigger_hydro(duration_s=global_sensor_state["ticks_remaining"], intensity=25.0)
                trigger_displacement(total_displacement_mm=10.0, duration_s=global_sensor_state["ticks_remaining"])
        
        if global_sensor_state["ticks_remaining"] <= 0:
            global_sensor_state.update({"event_active": False, "event_type": None, "phase": None})
            print("✅ EVENT END: System returning to normal state")
    seismic_data, hydro_data, displacement_data, env_data = get_seismic_readings(), get_hydro_readings(), get_displacement_readings(), get_environmental_readings()
    master_label = 1 if any([seismic_data["label"], hydro_data["label"], displacement_data["label"]]) else 0
    return {"timestamp": datetime.utcnow().isoformat(), **seismic_data, **hydro_data, **displacement_data, **env_data, "label": master_label, "event_active": global_sensor_state["event_active"], "event_phase": global_sensor_state["phase"], "event_type": global_sensor_state["event_type"]}