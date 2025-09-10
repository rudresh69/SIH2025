import time
import random
import sensors

# Configuration
EVENT_PROBABILITY_PER_SECOND = 0.02  # 2% chance per second
MIN_DURATION = 5                     # seconds
MAX_DURATION = 30                    # seconds
EVENT_TYPES = ["rockfall", "rainfall", "landslide"]
SAMPLE_RATE = 0.1                     # 10Hz simulation

print("Random Event Trigger Simulation Started (Ctrl+C to stop)...\n")

while True:
    # Randomly decide if we trigger an event
    if random.random() < EVENT_PROBABILITY_PER_SECOND:
        event_type = random.choice(EVENT_TYPES)
        duration = random.randint(MIN_DURATION, MAX_DURATION)
        print(f"⚠️  Random Event Triggered: {event_type} for {duration}s")
        sensors.trigger_all(event_type=event_type, duration_s=duration)

    # Print current readings (optional)
    readings = sensors.get_all_readings()
    print(readings)

    # Wait for next sample
    time.sleep(SAMPLE_RATE)
