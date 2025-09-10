"""
seismic.py -- Realistic seismic mock generator with proper state exposure for sensors.py
"""

import math
import random
import numpy as np
from datetime import datetime, timedelta

# ----------------- CONFIG -----------------
FS = 10
EVENT_RATE_PER_MIN = 1.0
MIN_COOLDOWN_S = 30
PRECURSOR_PROB = 0.2
PRECURSOR_MAX_S = 8
EVENT_MIN_S = 2.0
EVENT_MAX_S = 8.0
EVENT_MAG_MIN = 1.0
EVENT_MAG_MAX = 3.0
MACHINERY_PROB = 0.15
SEED = 42

random.seed(SEED)
np.random.seed(SEED)

# ----------------- STATE -----------------
seismic_state = {  # <-- exposed for sensors.py
    "t": 0,
    "last_event_time": None,
    "event": None,
    "precursor": None,
    "noise_level": 1.0,
    "scheduled_next": None,
    "sampling_interval_s": 1.0/FS
}

# ----------------- UTILS -----------------
def now():
    return datetime.utcnow()

def pink_noise(n, exponent=0.8):
    if n <= 4:
        return np.random.randn(n)
    white = np.random.randn(n)
    f = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, d=1.0/FS)
    freqs[0] = freqs[1] if len(freqs) > 1 else 1.0
    f = f / (freqs ** (exponent/2.0))
    pink = np.fft.irfft(f, n=n)
    if np.std(pink) == 0:
        return pink
    return (pink - np.mean(pink)) / (np.std(pink) + 1e-9)

# ----------------- EVENT SCHEDULING -----------------
def _schedule_next_event():
    rate_per_s = EVENT_RATE_PER_MIN / 60.0
    if rate_per_s <= 0:
        seismic_state["scheduled_next"] = None
        return
    inter_arrival_s = np.random.exponential(1.0 / rate_per_s)
    seismic_state["scheduled_next"] = now() + timedelta(seconds=inter_arrival_s)

def _can_schedule_event():
    if seismic_state["last_event_time"] is None:
        return True
    elapsed = (now() - seismic_state["last_event_time"]).total_seconds()
    return elapsed >= MIN_COOLDOWN_S

def _maybe_start_scheduled():
    if seismic_state["scheduled_next"] is None:
        _schedule_next_event()
        return
    if now() >= seismic_state["scheduled_next"] and _can_schedule_event():
        mag = random.uniform(EVENT_MAG_MIN, EVENT_MAG_MAX)
        dur_s = random.uniform(EVENT_MIN_S, EVENT_MAX_S)
        freq = random.uniform(2.0, 12.0)
        phase = random.uniform(0, 2*math.pi)
        ticks = int(max(1, round(dur_s * FS)))
        precursor = None
        if random.random() < PRECURSOR_PROB:
            pre_s = random.uniform(1.0, min(PRECURSOR_MAX_S, dur_s/2.0))
            precursor = {"remaining": int(pre_s * FS), "start_mag": mag * 0.15}
        seismic_state["event"] = {"remaining": ticks, "magnitude": mag, "phase": phase, "freq": freq}
        seismic_state["precursor"] = precursor
        seismic_state["scheduled_next"] = None
        seismic_state["last_event_time"] = now()

# ----------------- API -----------------
def trigger_event(magnitude=None, duration_s=None, precursor=False, freq=None):
    mag = magnitude if magnitude is not None else random.uniform(EVENT_MAG_MIN, EVENT_MAG_MAX)
    dur = duration_s if duration_s is not None else random.uniform(EVENT_MIN_S, EVENT_MAX_S)
    ticks = int(max(1, round(dur * FS)))
    f = freq if freq is not None else random.uniform(2.0, 12.0)
    phase = random.uniform(0, 2*math.pi)
    seismic_state["event"] = {"remaining": ticks, "magnitude": float(mag), "phase": phase, "freq": float(f)}
    if precursor:
        pre_s = min(PRECURSOR_MAX_S, dur/2.0)
        seismic_state["precursor"] = {"remaining": int(pre_s * FS), "start_mag": float(mag) * 0.15}
    else:
        seismic_state["precursor"] = None
    seismic_state["last_event_time"] = now()
    seismic_state["scheduled_next"] = None

def step():
    seismic_state['t'] += 1
    if seismic_state["scheduled_next"] is None:
        _schedule_next_event()
    _maybe_start_scheduled()
    if seismic_state.get("precursor"):
        seismic_state["precursor"]["remaining"] -= 1
        if seismic_state["precursor"]["remaining"] <= 0:
            seismic_state["precursor"] = None
    if seismic_state.get("event"):
        seismic_state["event"]["remaining"] -= 1
        if seismic_state["event"]["remaining"] <= 0:
            seismic_state["event"] = None
            seismic_state["last_event_time"] = now()

def get_readings():
    step()
    acc_b = np.random.normal(0, 0.02)
    geo_b = np.random.normal(0, 0.04)
    seis_b = np.random.normal(0, 0.01)
    mach = np.random.uniform(-0.03,0.03)
    acc = acc_b + mach
    geo = geo_b + mach*0.6
    seis = seis_b + mach*0.25

    if seismic_state.get("precursor"):
        pre = seismic_state["precursor"]
        pre_progress = max(0.0, pre["remaining"]) / max(1.0, int(PRECURSOR_MAX_S * FS))
        pre_amp = pre["start_mag"] * (1.0 - pre_progress)
        acc += pre_amp * math.sin(2*math.pi*1.5*seismic_state['t']/FS)
        geo += pre_amp * 0.8 * math.sin(2*math.pi*1.0*seismic_state['t']/FS)
        seis += pre_amp * 0.4 * math.sin(2*math.pi*0.8*seismic_state['t']/FS)

    if seismic_state.get("event"):
        ev = seismic_state["event"]
        t = seismic_state['t'] / FS
        base_wave = ev["magnitude"] * math.sin(2*math.pi*ev["freq"]*t + ev["phase"])
        acc += base_wave
        geo += base_wave * 1.6
        seis += base_wave * 0.45

    acc = float(np.clip(acc, -10.0, 10.0))
    geo = float(np.clip(geo, -20.0, 20.0))
    seis = float(np.clip(seis, -5.0, 5.0))

    label = 1 if (seismic_state.get("event") or seismic_state.get("precursor")) else 0

    return {
        "accelerometer": round(acc, 4),
        "geophone": round(geo, 4),
        "seismometer": round(seis, 4),
        "label": int(label)
    }

def is_event_active():
    return bool(seismic_state.get("event") or seismic_state.get("precursor"))

if __name__ == "__main__":
    import time
    _schedule_next_event()
    while True:
        r = get_readings()
        print(r)
        time.sleep(1.0/FS)
