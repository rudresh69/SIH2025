"""
rockfall_dataset_pipeline.py
This script generates a comprehensive, labeled dataset for the rockfall prediction model.
It runs the full sensor simulation, triggers random events, saves the
complete output to a CSV file, and provides a live visualization of the process.
"""
import sys
import os
import csv
import random
import time
from tqdm import tqdm
from collections import deque
import matplotlib.pyplot as plt

# -----------------------------
# Paths & Setup
# -----------------------------
# Add the parent directory (BACKEND) to the Python path to import from 'sensors'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from sensors import sensors

# Define the output path for the generated dataset
OUTPUT_CSV_FILE = os.path.join(BASE_DIR, "rockfall_dataset_refined.csv")


# =========================
# Configurations
# =========================
# Reduced sample count for a more manageable live demo. Increase for a larger dataset.
TOTAL_SAMPLES = 10000
EVENT_PROBABILITY = 0.005       # 0.5% chance per step to trigger a new random event.
EVENT_TYPES = ["rockfall", "rainfall", "landslide"]
MAX_PLOT_POINTS = 200           # Number of historical points to display on the live plot.


def generate_dataset_with_visualization():
    """
    Runs the main data generation loop. It calls the sensor aggregator,
    gets all readings, writes them to a CSV file, and displays a live plot.
    """
    print("Starting dataset generation process with live visualization...")
    print(f"This will create {TOTAL_SAMPLES} samples.")
    print(f"Output file: {OUTPUT_CSV_FILE}")

    headers = [
        "timestamp", "accelerometer", "geophone", "seismometer",
        "moisture_sensor", "piezometer", "crack_sensor", "inclinometer",
        "extensometer", "rain_sensor_mmhr", "temperature_celsius",
        "humidity_percent", "label"
    ]
    
    # --- Live Plot Setup ---
    sensor_groups = {
        "Seismic Sensors": ["accelerometer", "geophone", "seismometer"],
        "Displacement Sensors": ["crack_sensor", "inclinometer", "extensometer"],
        "Hydrological Sensors": ["moisture_sensor", "piezometer"],
        "Environmental Sensors": ["rain_sensor_mmhr", "temperature_celsius", "humidity_percent"]
    }
    
    plt.ion() # Turn on interactive mode
    fig, axs = plt.subplots(len(sensor_groups), 1, figsize=(15, 10), sharex=True)
    fig.suptitle("Live Sensor Data Generation", fontsize=16)

    lines = {}
    for i, (title, sensors_in_group) in enumerate(sensor_groups.items()):
        axs[i].set_title(title, loc='left', fontsize=10)
        axs[i].grid(True, linestyle='--', alpha=0.6)
        for sensor_name in sensors_in_group:
            lines[sensor_name], = axs[i].plot([], [], label=sensor_name, lw=1.5)
        # Add a line for the event label on the first plot
        if i == 0:
            lines['label'], = axs[i].plot([], [], label="EVENT ACTIVE", color='red', linestyle='--', lw=2)
        axs[i].legend(loc='upper left', fontsize=8)
    axs[-1].set_xlabel("Time Steps")

    # Deques for efficient, fixed-size data storage for plotting
    time_queue = deque(maxlen=MAX_PLOT_POINTS)
    label_queue = deque(maxlen=MAX_PLOT_POINTS)
    sensor_queues = {name: deque(maxlen=MAX_PLOT_POINTS) for name in lines if name != 'label'}
    # --- End Plot Setup ---

    try:
        with open(OUTPUT_CSV_FILE, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()

            for i in tqdm(range(TOTAL_SAMPLES), desc="Generating Data"):
                if random.random() < EVENT_PROBABILITY:
                    event_type = random.choice(EVENT_TYPES)
                    duration = random.randint(15, 60)
                    sensors.trigger_all(event_type=event_type, duration_s=duration)

                all_readings = sensors.get_all_readings()
                writer.writerow(all_readings)

                # --- Update Plot Data ---
                time_queue.append(i)
                # For plotting, scale the label to make it visible on the seismic chart
                label_value = all_readings['label'] * 5 
                label_queue.append(label_value if label_value > 0 else float('nan')) # Use NaN to create gaps
                
                for name, queue in sensor_queues.items():
                    queue.append(all_readings[name])

                # Update the data for each line on the plot
                for name, line in lines.items():
                    if name == 'label':
                        line.set_data(time_queue, label_queue)
                    else:
                        line.set_data(time_queue, sensor_queues[name])

                # Automatically adjust axis limits
                for ax in axs:
                    ax.relim()
                    ax.autoscale_view()
                
                # Redraw the canvas
                fig.canvas.draw()
                fig.canvas.flush_events()
                time.sleep(0.001) # A tiny pause to allow the plot to render

    except KeyboardInterrupt:
        print("\nDataset generation stopped by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return

    finally:
        plt.ioff() # Turn off interactive mode
        print("\n✅ Dataset generation complete.")
        print(f"Data saved to {os.path.abspath(OUTPUT_CSV_FILE)}")
        print("Closing plot window.")
        plt.close(fig) # Close the plot window

if __name__ == '__main__':
    generate_dataset_with_visualization()

