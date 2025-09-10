import csv
import time
import random
import sensors

# =========================
# Configurations
# =========================
FILENAME = "rockfall_dataset_random_events.csv"
TOTAL_SAMPLES = 5000       # Total dataset rows
SAMPLE_RATE = 0.1           # 10Hz simulation
EVENT_PROBABILITY = 0.02    # 2% chance to start an event per sample

# Event severity mapping
EVENT_SEVERITIES = {
    "low": {"label": 1, "min_duration": 5, "max_duration": 10},      # Warning
    "medium": {"label": 2, "min_duration": 10, "max_duration": 20},  # High Risk
    "high": {"label": 2, "min_duration": 20, "max_duration": 30}     # High Risk
}

EVENT_TYPES = ["rockfall", "rainfall", "landslide"]

# =========================
# Helper Functions
# =========================
def random_event():
    """Randomly choose event type and severity."""
    event_type = random.choice(EVENT_TYPES)
    severity = random.choice(list(EVENT_SEVERITIES.keys()))
    duration_range = EVENT_SEVERITIES[severity]
    duration = random.randint(duration_range["min_duration"], duration_range["max_duration"])
    label = duration_range["label"]
    return event_type, duration, label

# =========================
# Dataset Generation
# =========================
with open(FILENAME, "w", newline="") as csvfile:
    fieldnames = [
        "timestamp",
        "accelerometer", "geophone", "seismometer",
        "crack_sensor", "inclinometer", "extensometer",
        "moisture_sensor", "piezometer", "rain_sensor",
        "label"
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    print(f"Generating dataset with random events ({TOTAL_SAMPLES} samples)...")

    for i in range(TOTAL_SAMPLES):
        # Randomly trigger an event
        if random.random() < EVENT_PROBABILITY:
            event_type, duration, label = random_event()
            print(f"⚠️ Triggered {event_type} ({label}) for {duration}s at sample {i}")
            sensors.trigger_all(event_type=event_type, duration_s=duration)
        else:
            label = 0  # Normal reading

        # Capture sensor readings
        readings = sensors.get_all_readings()
        readings["timestamp"] = time.time()
        readings["label"] = max(label, readings.get("label", 0))  # Ensure event label overrides normal

        # Write to CSV
        writer.writerow(readings)

        # Wait for next sample
        time.sleep(SAMPLE_RATE)

print(f"Dataset generation complete! Saved to {FILENAME}")
