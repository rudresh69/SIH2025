import time
from . import seismic
from . import hydro
from . import displacement

# ----------------- GLOBAL EVENT TRIGGER -----------------
def trigger_all(event_type="rockfall", duration_s=30):
    """
    Trigger a global event affecting all sensor modules.
    event_type: "rockfall", "rainfall", "landslide"
    """

    if event_type == "rockfall":
        seismic.trigger_event(magnitude=2.0, duration_s=duration_s, precursor=True)
        hydro.trigger_event(moisture_increase=30, pressure_increase=20, duration_s=duration_s)
        displacement.trigger_event(crack_increase=4, tilt_increase=2, extensometer_increase=2, duration_s=duration_s)

    elif event_type == "rainfall":
        seismic.trigger_event(magnitude=1.0, duration_s=duration_s)
        hydro.trigger_event(moisture_increase=50, pressure_increase=30, duration_s=duration_s)
        displacement.trigger_event(crack_increase=1, tilt_increase=0.5, extensometer_increase=0.5, duration_s=duration_s)

    elif event_type == "landslide":
        seismic.trigger_event(magnitude=3.0, duration_s=duration_s, precursor=True)
        hydro.trigger_event(moisture_increase=40, pressure_increase=25, duration_s=duration_s)
        displacement.trigger_event(crack_increase=6, tilt_increase=3, extensometer_increase=4, duration_s=duration_s)

# ----------------- READ ALL SENSORS -----------------
def get_all_readings():
    """Get a single combined reading frame from all sensors."""

    seismic_readings = seismic.get_readings()
    hydro_readings = hydro.get_readings()
    disp_readings = displacement.get_readings()

    readings = {}
    readings.update(seismic_readings)
    readings.update(disp_readings)

    # Map hydro keys safely
    readings["moisture_sensor"] = hydro_readings.get("moisture", 0.0)
    readings["piezometer"] = hydro_readings.get("piezometer", 0.0)

    # Global event label (1 if any module in event mode)
    event_active = (
        seismic.is_event_active() or
        hydro.hydro_state.get("event") is not None or
        displacement.disp_state.get("event") is not None
    )
    readings["label"] = 1 if event_active else 0

    return readings

# ----------------- DEMO -----------------
if __name__ == "__main__":
    print("Unified Sensor Simulation (Ctrl+C to stop)...")
    time.sleep(1)

    # Start with normal conditions
    for _ in range(20):
        print(get_all_readings())
        time.sleep(0.1)

    # Trigger rockfall
    print("\n⚠️ Triggering ROCKFALL event...\n")
    trigger_all("rockfall", duration_s=20)

    try:
        while True:
            print(get_all_readings())
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopped unified sensor demo.")
