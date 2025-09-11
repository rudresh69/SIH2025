"""
seismic.py
A realistic seismic data generator for simulating earthquake events and background noise.

This module simulates readings from three common seismic sensors:
1.  Geophone (measures ground velocity)
2.  Accelerometer (measures ground acceleration)
3.  Seismometer (modeled here as measuring ground velocity)

Key Features:
-   **Realistic Waveforms:** Events are modeled with distinct P-waves, S-waves, and a decaying coda, not simple sine waves.
-   **Differentiated Physics:** Correctly models the physical relationship between velocity (geophone) and acceleration (accelerometer) by using numerical differentiation.
-   **Advanced Noise Model:** Uses pink noise for natural background microseisms and adds random cultural noise spikes (e.g., traffic, machinery).
-   **State Exposure:** The `seismic_state` dictionary is exposed for external modules to inspect the simulation's ground truth (e.g., if an event is active).
-   **Dynamic Scheduling:** Schedules random seismic events based on a configurable rate, with cooldown periods.
-   **Manual Triggering:** Allows for forcing an event with specific parameters using `trigger_event()`.
"""

import math
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

import numpy as np
from scipy.signal.windows import tukey

# ----------------- CONFIGURATION -----------------
FS: int = 20  # Sampling frequency in Hz
EVENT_RATE_PER_MIN: float = 0.8  # Average number of seismic events per minute
MIN_COOLDOWN_S: int = 45  # Minimum seconds between the end of one event and the start of another
PRECURSOR_PROB: float = 0.25  # Probability that an event will have a precursor signal
PRECURSOR_MAX_S: int = 10  # Maximum duration of a precursor in seconds
EVENT_MIN_S: float = 5.0  # Minimum duration of a seismic event in seconds
EVENT_MAX_S: float = 12.0  # Maximum duration of a seismic event in seconds
EVENT_MAG_MIN: float = 0.8  # Minimum magnitude of a seismic event
EVENT_MAG_MAX: float = 3.5  # Maximum magnitude of a seismic event
CULTURAL_NOISE_PROB: float = 0.02  # Chance per step of a sharp cultural noise spike
SEED: int = 42  # Random seed for reproducibility

# Initialize random seeds
random.seed(SEED)
np.random.seed(SEED)

# ----------------- SIMULATION STATE -----------------
# This dictionary holds the ground truth of the simulation at any given time.
seismic_state: Dict[str, Any] = {
    "t": 0,  # Global time tick counter
    "last_event_end_time": None,  # Timestamp of when the last event finished
    "event": None,  # Holds the active event's waveform data
    "precursor": None,  # Holds active precursor data
    "scheduled_next_event_time": None,  # Timestamp for the next scheduled event
    "sampling_interval_s": 1.0 / FS  # Time step between samples
}


# ----------------- UTILITY FUNCTIONS -----------------
def now() -> datetime:
    """Returns the current UTC time."""
    return datetime.utcnow()


def pink_noise(n: int, exponent: float = 1.0) -> np.ndarray:
    """
    Generates pink noise (1/f noise) of a given length.

    Args:
        n (int): The number of samples to generate.
        exponent (float): The frequency exponent (1.0 for pink noise).

    Returns:
        np.ndarray: A normalized array of pink noise.
    """
    if n <= 0:
        return np.array([])
    white = np.random.randn(n)
    f = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, d=1.0 / FS)
    freqs[0] = 1e-6  # Avoid division by zero at the DC component
    f_pink = f / (freqs** (exponent / 2.0))
    pink = np.fft.irfft(f_pink, n=n)
    if np.std(pink) == 0:
        return pink  # Avoid division by zero if std is zero
    return (pink - np.mean(pink)) / (np.std(pink) + 1e-9)


# ----------------- CORE EVENT LOGIC -----------------
def _generate_event_waveform(duration_ticks: int, magnitude: float) -> Dict[str, np.ndarray]:
    """
    Generates a realistic earthquake waveform with P-wave, S-wave, and coda.

    Args:
        duration_ticks (int): The total number of samples for the event.
        magnitude (float): The peak magnitude of the event.

    Returns:
        Dict[str, np.ndarray]: A dictionary containing the 'velocity' and 'acceleration' waveforms.
    """
    # 1. P-wave and S-wave setup
    p_wave_freq = random.uniform(FS * 0.2, FS * 0.3)  # Higher frequency
    s_wave_freq = random.uniform(FS * 0.05, FS * 0.15)  # Lower frequency
    s_arrival_offset = int(duration_ticks * random.uniform(0.1, 0.2))

    t = np.arange(duration_ticks) / FS
    p_wave = np.sin(2 * np.pi * p_wave_freq * t + random.uniform(0, 2 * np.pi))
    s_wave = np.sin(2 * np.pi * s_wave_freq * t + random.uniform(0, 2 * np.pi))

    # 2. Amplitude envelopes using a Tukey (tapered cosine) window
    p_env_len = min(duration_ticks, int(s_arrival_offset * 1.8))
    p_envelope = tukey(p_env_len, alpha=0.8) * magnitude * 0.6  # P-wave is weaker
    p_wave_packet = np.zeros(duration_ticks)
    p_wave_packet[:p_env_len] = p_wave[:p_env_len] * p_envelope

    s_env_len = duration_ticks - s_arrival_offset
    s_envelope = tukey(s_env_len, alpha=0.6) * magnitude  # S-wave is stronger
    s_wave_packet = np.zeros(duration_ticks)
    s_wave_packet[s_arrival_offset:] = s_wave[s_arrival_offset:] * s_envelope

    # 3. Combine waves and apply a final decay envelope for the coda
    velocity_waveform = p_wave_packet + s_wave_packet
    coda_decay = np.exp(-t / (duration_ticks / FS / 2.5))
    velocity_waveform *= coda_decay

    # 4. Differentiate velocity to get acceleration
    acceleration_waveform = np.gradient(velocity_waveform, seismic_state["sampling_interval_s"])

    return {"velocity": velocity_waveform, "acceleration": acceleration_waveform}


def _schedule_next_event() -> None:
    """Schedules the next random event based on the configured rate."""
    if EVENT_RATE_PER_MIN <= 0:
        return
    rate_per_s = EVENT_RATE_PER_MIN / 60.0
    inter_arrival_s = np.random.exponential(1.0 / rate_per_s)
    seismic_state["scheduled_next_event_time"] = now() + timedelta(seconds=inter_arrival_s)


def _maybe_start_scheduled_event() -> None:
    """Checks if a scheduled event should start and initiates it."""
    # Check if an event is already active
    if seismic_state["event"]:
        return

    # Check if it's time for the next scheduled event
    if seismic_state["scheduled_next_event_time"] and now() >= seismic_state["scheduled_next_event_time"]:
        # Check for cooldown period
        if seismic_state["last_event_end_time"]:
            elapsed = (now() - seismic_state["last_event_end_time"]).total_seconds()
            if elapsed < MIN_COOLDOWN_S:
                return  # Still in cooldown, do not start event

        mag = random.uniform(EVENT_MAG_MIN, EVENT_MAG_MAX)
        dur_s = random.uniform(EVENT_MIN_S, EVENT_MAX_S)
        trigger_event(magnitude=mag, duration_s=dur_s, precursor=random.random() < PRECURSOR_PROB)
        seismic_state["scheduled_next_event_time"] = None  # Clear schedule after starting


# ----------------- PUBLIC API -----------------
def trigger_event(magnitude: float, duration_s: float, precursor: bool) -> None:
    """
    Manually triggers a seismic event with specified parameters.

    Args:
        magnitude (float): The peak magnitude for the event.
        duration_s (float): The duration of the event in seconds.
        precursor (bool): Whether to generate a precursor signal.
    """
    ticks = int(max(1, round(duration_s * FS)))
    waveforms = _generate_event_waveform(ticks, magnitude)

    seismic_state["event"] = {
        "remaining_ticks": ticks,
        "waveform_v": waveforms["velocity"],
        "waveform_a": waveforms["acceleration"],
        "cursor": 0
    }
    if precursor:
        pre_s = random.uniform(2.0, min(PRECURSOR_MAX_S, duration_s / 2.0))
        seismic_state["precursor"] = {
            "remaining_ticks": int(pre_s * FS),
            "start_mag": float(magnitude) * 0.15
        }
    else:
        seismic_state["precursor"] = None


def step() -> None:
    """Advances the simulation by one time step."""
    seismic_state['t'] += 1
    if seismic_state["scheduled_next_event_time"] is None and EVENT_RATE_PER_MIN > 0:
        _schedule_next_event()
    _maybe_start_scheduled_event()

    if seismic_state.get("precursor"):
        pre = seismic_state["precursor"]
        pre["remaining_ticks"] -= 1
        if pre["remaining_ticks"] <= 0:
            seismic_state["precursor"] = None

    if seismic_state.get("event"):
        ev = seismic_state["event"]
        ev["remaining_ticks"] -= 1
        ev["cursor"] += 1
        if ev["remaining_ticks"] <= 0:
            seismic_state["event"] = None
            seismic_state["last_event_end_time"] = now()


def get_readings() -> Dict[str, Any]:
    """
    Advances the simulation one step and returns the new sensor readings.

    Returns:
        Dict[str, Any]: A dictionary containing 'accelerometer', 'geophone',
                        'seismometer' readings, and a binary 'label'.
    """
    step()

    # 1. Generate realistic background noise
    base_noise = pink_noise(1, exponent=1.2)[0] * 0.02
    acc_noise = base_noise + np.random.normal(0, 0.015)
    geo_noise = base_noise * 1.2 + np.random.normal(0, 0.025)
    seis_noise = base_noise * 0.8 + np.random.normal(0, 0.01)

    # 2. Add random cultural noise spikes
    if random.random() < CULTURAL_NOISE_PROB:
        spike = (random.random() - 0.5) * 0.25
        acc_noise += spike
        geo_noise += spike * 0.8

    acc, geo, seis = acc_noise, geo_noise, seis_noise

    # 3. Add precursor signal if active
    if seismic_state.get("precursor"):
        pre = seismic_state["precursor"]
        t = seismic_state['t']
        pre_amp = pre["start_mag"] * (pre["remaining_ticks"] / (PRECURSOR_MAX_S * FS))
        geo += pre_amp * 0.8 * math.sin(2 * math.pi * 1.0 * t / FS)
        acc += pre_amp * math.sin(2 * math.pi * 1.5 * t / FS)
        seis += pre_amp * 0.4 * math.sin(2 * math.pi * 0.8 * t / FS)

    # 4. Add main event signal if active
    if seismic_state.get("event"):
        ev = seismic_state["event"]
        cursor = ev["cursor"]
        if cursor < len(ev["waveform_v"]):
            velocity_signal = ev["waveform_v"][cursor]
            acceleration_signal = ev["waveform_a"][cursor]

            geo += velocity_signal
            seis += velocity_signal * 0.5  # Seismometer has different gain
            acc += acceleration_signal

    # 5. Final clipping and formatting
    label = 1 if (seismic_state.get("event") or seismic_state.get("precursor")) else 0

    return {
        "accelerometer": round(float(np.clip(acc, -10.0, 10.0)), 5),
        "geophone": round(float(np.clip(geo, -20.0, 20.0)), 5),
        "seismometer": round(float(np.clip(seis, -5.0, 5.0)), 5),
        "label": int(label)
    }


def is_event_active() -> bool:
    """Returns True if a precursor or main event is currently active."""
    return bool(seismic_state.get("event") or seismic_state.get("precursor"))


# ----------------- EXECUTION EXAMPLE -----------------
if __name__ == "__main__":
    print("Starting seismic simulation. Press Ctrl+C to exit.")
    print("Timestamp (UTC)           | Geophone   | Accelerometer | Event Active")
    print("-" * 75)

    # Example of manually triggering a large event at the start
    # trigger_event(magnitude=3.0, duration_s=10.0, precursor=True)

    while True:
        try:
            readings = get_readings()
            ts = now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            geo_val = readings['geophone']
            acc_val = readings['accelerometer']
            active_marker = " * EVENT * " if readings['label'] == 1 else ""

            # Simple text visualization
            geo_bar = '#' * int(abs(geo_val) * 10)
            acc_bar = 'x' * int(abs(acc_val) * 10)

            print(
                f"{ts} | {geo_val: 8.4f} | {acc_val: 13.4f} | {active_marker}"
            )

            time.sleep(seismic_state["sampling_interval_s"])
        except KeyboardInterrupt:
            print("\nSimulation stopped.")
            break
