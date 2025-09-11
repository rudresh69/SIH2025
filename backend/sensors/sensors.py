"""
sensors.py
Master sensor aggregator for the rockfall monitoring system.

This module imports all individual sensor simulation modules (seismic, hydro,
displacement, environmental) and provides a single, unified function to
retrieve a complete, timestamped reading from all of them. It also includes
a utility to trigger coordinated, realistic event scenarios.
"""

import time
from datetime import datetime
from typing import Dict, Any

# Import all individual sensor modules
from . import seismic
from . import hydro
from . import displacement
from . import environmental

# ----------------- GLOBAL EVENT TRIGGER -----------------
def trigger_all(event_type: str = "rockfall", duration_s: int = 30) -> None:
    """
    Triggers a coordinated event across relevant sensor modules.

    This function simulates realistic scenarios by activating different sensors
    with appropriate parameters based on the event type.

    Args:
        event_type (str): The type of event to simulate.
                          Options: "rockfall", "rainfall", "landslide".
        duration_s (int): The approximate duration for the event's effects.
    """
    print(f"\n--- TRIGGERING GLOBAL EVENT: {event_type.upper()} ---")

    if event_type == "rockfall":
        # A typical rockfall: sharp seismic signal, moderate displacement.
        # Hydro response is minimal unless preceded by rain.
        seismic.trigger_event(magnitude=2.5, duration_s=duration_s, precursor=True)
        displacement.trigger_event(total_displacement_mm=3.0, duration_s=duration_s * 2) # Displacement can be slower

    elif event_type == "rainfall":
        # A heavy rainfall event: no seismic trigger, but high hydro response
        # leading to potential for minor, slow displacement (creep).
        hydro.trigger_event(duration_s=duration_s, intensity=25.0) # High intensity rain
        # Simulate a small, slow creep due to saturation
        displacement.trigger_event(total_displacement_mm=0.5, duration_s=duration_s * 5)

    elif event_type == "landslide":
        # A major landslide: strong, long seismic signal, major displacement,
        # and often occurs in saturated ground conditions.
        seismic.trigger_event(magnitude=3.5, duration_s=duration_s, precursor=True)
        hydro.trigger_event(duration_s=duration_s, intensity=15.0) # Assume ground is already saturated
        displacement.trigger_event(total_displacement_mm=10.0, duration_s=duration_s)

# ----------------- READ ALL SENSORS -----------------
def get_all_readings() -> Dict[str, Any]:
    """
    Gathers readings from all sensor modules and combines them into a single dictionary.

    It also computes a master 'label' for the data point. The label is 1 (event)
    if any of the primary risk sensors (seismic, hydro, displacement) indicate an
    active event. The environmental data is treated as contextual information.

    Returns:
        Dict[str, Any]: A flat dictionary containing all sensor readings, a timestamp,
                        and a master event label.
    """
    # 1. Get readings from each sensor module
    seismic_data = seismic.get_readings()
    hydro_data = hydro.get_readings()
    displacement_data = displacement.get_readings()
    env_data = environmental.get_readings()

    # 2. Determine the master label
    # An event is active if seismic, hydro, OR displacement sensors report it.
    is_event_active = any([
        seismic_data.get("label", 0),
        hydro_data.get("label", 0),
        displacement_data.get("label", 0)
    ])
    master_label = 1 if is_event_active else 0

    # 3. Combine all data into a single, flat dictionary.
    # The order of features here will be the order in your CSV and for your model.
    all_data = {
        "timestamp": datetime.utcnow().isoformat(),

        # Seismic Features
        "accelerometer": seismic_data["accelerometer"],
        "geophone": seismic_data["geophone"],
        "seismometer": seismic_data["seismometer"],

        # Hydrological Features
        "moisture_sensor": hydro_data["moisture_sensor"],
        "piezometer": hydro_data["piezometer"],

        # Displacement Features
        "crack_sensor": displacement_data["crack_sensor"],
        "inclinometer": displacement_data["inclinometer"],
        "extensometer": displacement_data["extensometer"],

        # Environmental Features
        "rain_sensor_mmhr": env_data["rain_sensor_mmhr"],
        "temperature_celsius": env_data["temperature_celsius"],
        "humidity_percent": env_data["humidity_percent"],

        # Master Label
        "label": master_label
    }

    return all_data

# ----------------- DEMO -----------------
if __name__ == "__main__":
    print("Starting combined sensor feed demo. Press Ctrl+C to stop.")
    # Use the sampling interval from your fastest sensor for the demo loop
    sampling_interval = seismic.seismic_state['sampling_interval_s']

    print("\n--- Phase 1: Normal Conditions ---")
    time.sleep(1)
    for _ in range(50):
        readings = get_all_readings()
        print(f"Time: {readings['timestamp'][11:23]}, "
              f"Geophone: {readings['geophone']:.3f}, "
              f"Moisture: {readings['moisture_sensor']:.2f}%, "
              f"Rain: {readings['rain_sensor_mmhr']:.1f} mm/hr, "
              f"Label: {readings['label']}")
        time.sleep(sampling_interval)

    # Trigger a coordinated event
    trigger_all("rockfall", duration_s=15)
    print("\n--- Phase 2: Rockfall Event Active ---")

    try:
        # Run for a while to observe the event and its aftermath
        for _ in range(300):
            readings = get_all_readings()
            event_marker = " *EVENT ACTIVE*" if readings['label'] == 1 else ""
            print(f"Time: {readings['timestamp'][11:23]}, "
                  f"Geophone: {readings['geophone']:.3f}, "
                  f"Moisture: {readings['moisture_sensor']:.2f}%, "
                  f"Rain: {readings['rain_sensor_mmhr']:.1f} mm/hr, "
                  f"Label: {readings['label']}{event_marker}")
            time.sleep(sampling_interval)
    except KeyboardInterrupt:
        print("\nSimulation stopped.")
