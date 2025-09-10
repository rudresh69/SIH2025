import time
import seismic
import hydro
import displacement

# Global state
sensor_state = {
    "event": None
}

def trigger_all(event_type="rockfall", duration_s=30):
    """
    Trigger a global event affecting all sensor modules.
    event_type: "rockfall", "rainfall", "landslide"
    """
    sensor_state["event"] = {
        "type": event_type,
        "remaining": duration_s * 10  # simulate at 10Hz
    }

    # Trigger each module with appropriate parameters
    if event_type == "rockfall":
        seismic.trigger_event(acc_increase=1.5, geo_increase=2.5, seis_increase=0.8, duration_s=duration_s)
        hydro.trigger_event(moisture_increase=30, piezo_increase=20, duration_s=duration_s)
        displacement.trigger_event(crack_increase=4, tilt_increase=2, extensometer_increase=2, duration_s=duration_s)

    elif event_type == "rainfall":
        seismic.trigger_event(acc_increase=0.5, geo_increase=1.0, seis_increase=0.3, duration_s=duration_s)
        hydro.trigger_event(moisture_increase=50, piezo_increase=30, duration_s=duration_s)
        displacement.trigger_event(crack_increase=1, tilt_increase=0.5, extensometer_increase=0.5, duration_s=duration_s)

    elif event_type == "landslide":
        seismic.trigger_event(acc_increase=2.0, geo_increase=3.5, seis_increase=1.5, duration_s=duration_s)
        hydro.trigger_event(moisture_increase=40, piezo_increase=25, duration_s=duration_s)
        displacement.trigger_event(crack_increase=6, tilt_increase=3, extensometer_increase=4, duration_s=duration_s)

def get_all_readings():
    """Get a single combined reading frame from all sensors."""
    readings = {}
    readings.update(seismic.get_readings())
    readings.update(hydro.get_readings())
    readings.update(displacement.get_readings())

    # Global event label (1 if any module in event mode)
    label = 1 if (seismic.seismic_state["event"] or 
                  hydro.hydro_state["event"] or 
                  displacement.disp_state["event"]) else 0
    readings["label"] = label
    return readings

# Demo loop
if __name__ == "__main__":
    print("Unified Sensor Simulation (Ctrl+C to stop)...")
    time.sleep(1)

    # Start with normal conditions
    for i in range(20):
        print(get_all_readings())
        time.sleep(0.1)

    # Trigger rockfall
    print("\n⚠️ Triggering ROCKFALL event...\n")
    trigger_all("rockfall", duration_s=20)

    while True:
        print(get_all_readings())
        time.sleep(0.1)
