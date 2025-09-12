"""
sensors.py
Master sensor aggregator for the rockfall monitoring system with
early-warning phase support and gradual sensor trends.
"""

import random
from typing import Dict, Any
from datetime import datetime

# Import individual sensor modules
from . import seismic
from . import hydro
from . import displacement
from . import environmental

# ----------------- GLOBAL STATE -----------------
# Tracks current events and their phases
sensor_state: Dict[str, Any] = {
    "event_active": False,
    "event_type": None,
    "phase": None,               # 'early_warning' or 'main_event'
    "ticks_remaining": 0,
    "phase_transition_tick": 0
}

# ----------------- EVENT TRIGGER -----------------
def trigger_all(event_type: str = "rockfall", duration_s: int = 60) -> None:
    """
    Triggers a coordinated event with early-warning and main event phases.
    """
    print(f"\n--- TRIGGERING GLOBAL EVENT: {event_type.upper()} ({duration_s}s) ---")

    total_ticks = duration_s
    early_phase_ticks = int(duration_s * 0.66)
    main_phase_ticks = total_ticks - early_phase_ticks

    # Initialize global sensor_state
    sensor_state.update({
        "event_active": True,
        "event_type": event_type,
        "phase": "early_warning",
        "ticks_remaining": total_ticks,
        "phase_transition_tick": main_phase_ticks  # when early warning ends
    })

    # Initialize event sensors depending on type
    if event_type == "rockfall":
        seismic.trigger_event(magnitude=1.0, duration_s=early_phase_ticks, precursor=True)  # small tremor
        displacement.trigger_event(total_displacement_mm=0.5, duration_s=early_phase_ticks)  # slow creep
    elif event_type == "rainfall":
        hydro.trigger_event(duration_s=duration_s, intensity=25.0)
        displacement.trigger_event(total_displacement_mm=0.2, duration_s=duration_s)
    elif event_type == "landslide":
        seismic.trigger_event(magnitude=1.5, duration_s=early_phase_ticks, precursor=True)
        hydro.trigger_event(duration_s=duration_s, intensity=15.0)
        displacement.trigger_event(total_displacement_mm=1.0, duration_s=early_phase_ticks)

# ----------------- SENSOR READING -----------------
def get_all_readings() -> Dict[str, Any]:
    """
    Gather readings from all sensors, apply event phase adjustments,
    and update global event state.
    """
    # ----------------- UPDATE EVENT STATE -----------------
    if sensor_state["event_active"]:
        sensor_state["ticks_remaining"] -= 1

        # Check for phase transition
        if sensor_state["phase"] == "early_warning" and sensor_state["ticks_remaining"] <= sensor_state["phase_transition_tick"]:
            sensor_state["phase"] = "main_event"
            # Update sensors for main event
            if sensor_state["event_type"] == "rockfall":
                seismic.trigger_event(magnitude=3.0, duration_s=sensor_state["ticks_remaining"], precursor=False)
                displacement.trigger_event(total_displacement_mm=2.5, duration_s=sensor_state["ticks_remaining"])
            elif sensor_state["event_type"] == "landslide":
                seismic.trigger_event(magnitude=3.5, duration_s=sensor_state["ticks_remaining"], precursor=False)
                displacement.trigger_event(total_displacement_mm=10.0, duration_s=sensor_state["ticks_remaining"])

        # End event
        if sensor_state["ticks_remaining"] <= 0:
            sensor_state.update({
                "event_active": False,
                "event_type": None,
                "phase": None,
                "ticks_remaining": 0,
                "phase_transition_tick": 0
            })

    # ----------------- GET SENSOR READINGS -----------------
    seismic_data = seismic.get_readings()
    hydro_data = hydro.get_readings()
    displacement_data = displacement.get_readings()
    env_data = environmental.get_readings()

    # ----------------- MASTER LABEL -----------------
    # Event active if any primary sensor shows event signal
    is_event_active = any([
        seismic_data.get("label", 0),
        hydro_data.get("label", 0),
        displacement_data.get("label", 0)
    ])
    master_label = 1 if is_event_active else 0

    # ----------------- COMBINE INTO SINGLE DICT -----------------
    all_data = {
        "timestamp": datetime.utcnow().isoformat(),

        # Seismic
        "accelerometer": seismic_data["accelerometer"],
        "geophone": seismic_data["geophone"],
        "seismometer": seismic_data["seismometer"],

        # Hydrological
        "moisture_sensor": hydro_data["moisture_sensor"],
        "piezometer": hydro_data["piezometer"],

        # Displacement
        "crack_sensor": displacement_data["crack_sensor"],
        "inclinometer": displacement_data["inclinometer"],
        "extensometer": displacement_data["extensometer"],

        # Environmental
        "rain_sensor_mmhr": env_data["rain_sensor_mmhr"],
        "temperature_celsius": env_data["temperature_celsius"],
        "humidity_percent": env_data["humidity_percent"],

        # Master Label
        "label": master_label
    }

    return all_data

# ----------------- DEMO -----------------
if __name__ == "__main__":
    import time
    print("Starting enhanced sensors demo (early-warning + main event)...")
    for i in range(200):
        if i == 50:
            trigger_all("rockfall", duration_s=60)
        data = get_all_readings()
        print(f"{i:03d} | Acc:{data['accelerometer']:.2f}, Geo:{data['geophone']:.2f}, "
              f"Moisture:{data['moisture_sensor']:.2f}, Label:{data['label']}, Phase:{sensor_state['phase']}")
        time.sleep(0.05)
