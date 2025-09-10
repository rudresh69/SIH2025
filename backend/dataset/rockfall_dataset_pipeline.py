# rockfall_dataset_pipeline.py
import sys
import os
import csv
import time
import random
from collections import deque
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATASET_PATH = os.path.join(BASE_DIR, "rockfall_dataset_random_events.csv")
REFINED_DATASET_PATH = os.path.join(BASE_DIR, "rockfall_dataset_refined.csv")
X_PATH = os.path.join(BASE_DIR, "X_windows.npy")
Y_PATH = os.path.join(BASE_DIR, "y_windows.npy")

# Add backend folder to path so we can import sensors
sys.path.append(BASE_DIR)
from sensors.sensors import get_all_readings, trigger_all

# =========================
# Configurations
# =========================
TOTAL_SAMPLES = 10000
SAMPLE_RATE = 0.1  # 10Hz simulation
EVENT_PROBABILITY = 0.02  # 2% chance per sample
MAX_POINTS = 100  # Max points for live plot

EVENT_SEVERITIES = {
    "low": {"label": 1, "min_duration": 5, "max_duration": 10},
    "medium": {"label": 2, "min_duration": 10, "max_duration": 20},
    "high": {"label": 2, "min_duration": 20, "max_duration": 30}
}
EVENT_TYPES = ["rockfall", "rainfall", "landslide"]

SENSOR_COLS = [
    "accelerometer", "geophone", "seismometer",
    "crack_sensor", "inclinometer", "extensometer",
    "moisture_sensor", "piezometer"
]

# =========================
# Helper Functions
# =========================
def random_event():
    event_type = random.choice(EVENT_TYPES)
    severity = random.choice(list(EVENT_SEVERITIES.keys()))
    duration_range = EVENT_SEVERITIES[severity]
    duration = random.randint(duration_range["min_duration"], duration_range["max_duration"])
    label = duration_range["label"]
    return event_type, duration, label

def print_progress(current, total):
    bar_length = 40
    filled_length = int(bar_length * current // total)
    bar = "█" * filled_length + "-" * (bar_length - filled_length)
    print(f"\rProgress: |{bar}| {current}/{total} samples", end="", flush=True)

def refine_labels(df):
    df['event_type'] = 0    # 0 = Normal, 1=Rockfall, 2=Rainfall, 3=Landslide
    df['severity'] = 'None' # None / Low / Medium / High
    for idx, row in df.iterrows():
        if row['label'] == 0:
            continue  # Normal
        # Rockfall: seismic spike or displacement
        if row['accelerometer'] > 0.05 or row['crack_sensor'] > 0.02:
            df.at[idx, 'event_type'] = 1
            df.at[idx, 'severity'] = 'High' if row['accelerometer'] > 0.1 else 'Medium'
        # Rainfall: hydro spike
        elif row['moisture_sensor'] > 0.7 or row['piezometer'] > 0.8:
            df.at[idx, 'event_type'] = 2
            df.at[idx, 'severity'] = 'High' if row['moisture_sensor'] > 0.85 else 'Medium'
        # Landslide: combination of seismic + hydro + displacement
        elif (row['accelerometer'] > 0.03 and row['moisture_sensor'] > 0.6 and row['crack_sensor'] > 0.01):
            df.at[idx, 'event_type'] = 3
            df.at[idx, 'severity'] = 'High' if row['accelerometer'] > 0.07 else 'Medium'
    return df

def create_windows(X, y, window_size=10):
    X_windows, y_windows = [], []
    for i in range(len(X)-window_size):
        X_windows.append(X.iloc[i:i+window_size].values.flatten())
        y_windows.append(y.iloc[i:i+window_size].mode()[0])
    return np.array(X_windows), np.array(y_windows)

def inject_precursor(window):
    """Gradually increase values in last few timesteps to simulate pre-event."""
    window = window.copy()
    T = window.shape[0]
    window[-5:, 0] += np.linspace(0, 0.5, 5)   # accelerometer
    window[-5:, 2] += np.linspace(0, 0.3, 5)   # seismometer
    window[-5:, 3] += np.linspace(0, 0.3, 5)   # crack_sensor
    window[-5:, 6] += np.linspace(0, 0.2, 5)   # moisture_sensor
    return window

# =========================
# Step 1: Generate Live Dataset
# =========================
csvfile = open(RAW_DATASET_PATH, "w", newline="")
writer = csv.DictWriter(csvfile, fieldnames=SENSOR_COLS + ["timestamp", "label"])
writer.writeheader()

time_queue = deque(maxlen=MAX_POINTS)
sensor_queues = {col: deque(maxlen=MAX_POINTS) for col in SENSOR_COLS}
labels_queue = deque(maxlen=MAX_POINTS)

plt.ion()
fig, axs = plt.subplots(3,1, figsize=(12,10), sharex=True)
axs[0].set_title("Seismic Sensors"); axs[0].set_ylabel("Accel/m/s²")
axs[1].set_title("Displacement Sensors"); axs[1].set_ylabel("Crack/Tilt/Ext")
axs[2].set_title("Hydro Sensors"); axs[2].set_ylabel("Moisture/Piezometer"); axs[2].set_xlabel("Time (s)")

lines = {}
for col, ax in zip(SENSOR_COLS[:3], [axs[0]]*3):
    lines[col], = ax.plot([], [], label=col)
for col, ax in zip(SENSOR_COLS[3:6], [axs[1]]*3):
    lines[col], = ax.plot([], [], label=col)
for col, ax in zip(SENSOR_COLS[6:], [axs[2]]*2):
    lines[col], = ax.plot([], [], label=col)
lines['label'], = axs[2].plot([], [], label="Event", linestyle='--', color='red')
for ax in axs: ax.legend()

start_time = time.time()
print("✅ Live Dataset Generation Started...")

for i in range(TOTAL_SAMPLES):
    if random.random() < EVENT_PROBABILITY:
        event_type, duration, ev_label = random_event()
        print(f"\n⚠️ Triggered {event_type} ({ev_label}) for {duration}s at sample {i}")
        trigger_all(event_type=event_type, duration_s=duration)

    readings = get_all_readings()
    readings["timestamp"] = time.time()
    writer.writerow(readings)

    # Update queues
    current_time = time.time() - start_time
    time_queue.append(current_time)
    for col in SENSOR_COLS: sensor_queues[col].append(readings[col])
    labels_queue.append(readings["label"])

    # Update plots
    for col in SENSOR_COLS[:3]: lines[col].set_data(time_queue, sensor_queues[col])
    for col in SENSOR_COLS[3:6]: lines[col].set_data(time_queue, sensor_queues[col])
    for col in SENSOR_COLS[6:]: lines[col].set_data(time_queue, sensor_queues[col])
    lines['label'].set_data(time_queue, labels_queue)
    for ax in axs: ax.relim(); ax.autoscale_view()
    plt.pause(SAMPLE_RATE)
    print_progress(i+1, TOTAL_SAMPLES)
    time.sleep(SAMPLE_RATE)

csvfile.close()
print(f"\n✅ Dataset saved to {RAW_DATASET_PATH}")

# =========================
# Step 2: Refine Labels
# =========================
df = pd.read_csv(RAW_DATASET_PATH)
df = refine_labels(df)
df.to_csv(REFINED_DATASET_PATH, index=False)
print(f"✅ Refined dataset saved to {REFINED_DATASET_PATH}")

# =========================
# Step 3: Generate Precursor Windows
# =========================
neg_df = df[df['event_type']==0].reset_index(drop=True)
window_length = 50
num_positive_samples = 5000

positive_windows = []
for _ in range(num_positive_samples):
    idx = np.random.randint(0, len(neg_df)-window_length)
    window = neg_df[SENSOR_COLS].iloc[idx:idx+window_length].values
    window = inject_precursor(window)
    positive_windows.append(window)
positive_windows = np.array(positive_windows)

negative_windows = []
for _ in range(num_positive_samples):
    idx = np.random.randint(0, len(neg_df)-window_length)
    window = neg_df[SENSOR_COLS].iloc[idx:idx+window_length].values
    negative_windows.append(window)
negative_windows = np.array(negative_windows)

X = np.concatenate([positive_windows, negative_windows], axis=0)
y = np.concatenate([np.ones(len(positive_windows)), np.zeros(len(negative_windows))], axis=0)

np.save(X_PATH, X)
np.save(Y_PATH, y)
print(f"✅ Windowed dataset saved to {X_PATH}, {Y_PATH}")

# =========================
# Step 4: Optional Analysis & Sliding Windows for ML
# =========================
window_size = 10
X_win, y_win = create_windows(df[SENSOR_COLS], df['event_type'], window_size)
print(f"\nSliding-window features shape: {X_win.shape}, targets shape: {y_win.shape}")

print("\n✅ Pipeline Complete!")
