"""
seismic.py -- Improved realistic seismic mock generator for prototype + dataset.
Features:
 - Quiet baseline (Gaussian + pink-ish noise)
 - Sparse event scheduling using Poisson-like probability (controlled rate)
 - Optional precursor (ramp-up) before event
 - Event state with decaying waveform applied to accel/geo/seis (different scales)
 - Cooldown after events to avoid bursts of frequent events
 - Manual trigger API-friendly: trigger_event(magnitude, duration, precursor)
 - get_readings() returns readings + label (0/1)
 - configure(...) functions to change behavior at runtime
"""

import math
import random
import numpy as np
from datetime import datetime, timedelta

# ----------------- CONFIGURABLE PARAMETERS -----------------
FS = 10                     # sampling frequency in Hz for real-time streaming (10Hz recommended for demo)
EVENT_RATE_PER_MIN = 1.0    # expected events per minute (Poisson rate) -> adjust to be rare
MIN_COOLDOWN_S = 30         # minimum seconds after event before new scheduled event allowed
PRECURSOR_PROB = 0.2        # probability an event has a precursor ramp
PRECURSOR_MAX_S = 8         # max precursor length in seconds
EVENT_MIN_S = 2.0
EVENT_MAX_S = 8.0
EVENT_MAG_MIN = 1.0
EVENT_MAG_MAX = 3.0
MACHINERY_PROB = 0.15       # occasional narrowband interference probability
SEED = 42

random.seed(SEED)
np.random.seed(SEED)

# ----------------- INTERNAL STATE -----------------
state = {
    "t": 0,                      # discrete tick counter
    "last_event_time": None,     # UTC datetime of last event
    "event": None,               # dict if event active: {'remaining':n_ticks, 'magnitude':x, 'phase':y, 'freq':f}
    "precursor": None,           # dict if precursor active
    "noise_level": 1.0,          # multiplier for general baseline noise
    "scheduled_next": None,      # next scheduled event time (datetime) if using scheduler
    "sampling_interval_s": 1.0/FS
}

# ----------------- UTILS -----------------
def now():
    return datetime.utcnow()

def pink_noise(n, exponent=0.8):
    """Simple 1/f-ish pink noise generator for a short vector (returns numpy array)."""
    # small n -> fallback to gaussian
    if n <= 4:
        return np.random.randn(n)
    white = np.random.randn(n)
    f = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, d=1.0/FS)
    freqs[0] = freqs[1] if len(freqs)>1 else 1.0
    f = f / (freqs ** (exponent/2.0))
    pink = np.fft.irfft(f, n=n)
    if np.std(pink) == 0:
        return pink
    return (pink - np.mean(pink)) / (np.std(pink) + 1e-9)

# ----------------- SCHEDULER / STATE MACHINE -----------------
def _schedule_next_event():
    """Set scheduled_next based on Poisson process (exponential inter-arrival)."""
    # rate per second
    rate_per_s = EVENT_RATE_PER_MIN / 60.0
    if rate_per_s <= 0:
        state["scheduled_next"] = None
        return
    # sample inter-arrival in seconds from exponential distribution
    inter_arrival_s = np.random.exponential(1.0 / rate_per_s)
    state["scheduled_next"] = now() + timedelta(seconds=inter_arrival_s)

def _can_schedule_event():
    """Check cooldown constraint."""
    if state["last_event_time"] is None:
        return True
    elapsed = (now() - state["last_event_time"]).total_seconds()
    return elapsed >= MIN_COOLDOWN_S

def _maybe_start_scheduled():
    """Start a scheduled event if scheduled_next reached and cooldown satisfied."""
    if state["scheduled_next"] is None:
        _schedule_next_event()
        return
    if now() >= state["scheduled_next"] and _can_schedule_event():
        # start an event (with optional precursor)
        mag = random.uniform(EVENT_MAG_MIN, EVENT_MAG_MAX)
        dur_s = random.uniform(EVENT_MIN_S, EVENT_MAX_S)
        freq = random.uniform(2.0, 12.0)  # Hz band for event waveform (demo-friendly)
        phase = random.uniform(0, 2*math.pi)
        ticks = int(max(1, round(dur_s * FS)))
        # decide if precursor
        precursor = None
        if random.random() < PRECURSOR_PROB:
            pre_s = random.uniform(1.0, min(PRECURSOR_MAX_S, dur_s/2.0))
            precursor = {"remaining": int(pre_s * FS), "start_mag": mag * 0.15}
        # commit event state
        state["event"] = {"remaining": ticks, "magnitude": mag, "phase": phase, "freq": freq}
        state["precursor"] = precursor
        state["scheduled_next"] = None
        # enforce cooldown by recording last_event_time now (start)
        state["last_event_time"] = now()

# ----------------- PUBLIC CONFIG FUNCTIONS -----------------
def configure(event_rate_per_min=None, min_cooldown_s=None, fs=None, noise_level=None):
    """Runtime configuration for demo tuning."""
    global FS
    if event_rate_per_min is not None:
        state_rate = float(event_rate_per_min)
        # just set global
        globals()['EVENT_RATE_PER_MIN'] = event_rate_per_min
    if min_cooldown_s is not None:
        globals()['MIN_COOLDOWN_S'] = min_cooldown_s
    if fs is not None:
        globals()['FS'] = int(fs)
        state['sampling_interval_s'] = 1.0 / globals()['FS']
    if noise_level is not None:
        state['noise_level'] = float(noise_level)

def trigger_event(magnitude=None, duration_s=None, precursor=False, freq=None):
    """Manual trigger: immediately start an event (useful for demo button)."""
    mag = magnitude if magnitude is not None else random.uniform(EVENT_MAG_MIN, EVENT_MAG_MAX)
    dur = duration_s if duration_s is not None else random.uniform(EVENT_MIN_S, EVENT_MAX_S)
    ticks = int(max(1, round(dur * FS)))
    f = freq if freq is not None else random.uniform(2.0, 12.0)
    phase = random.uniform(0, 2*math.pi)
    state["event"] = {"remaining": ticks, "magnitude": float(mag), "phase": phase, "freq": float(f)}
    if precursor:
        pre_s = min(PRECURSOR_MAX_S, dur/2.0)
        state["precursor"] = {"remaining": int(pre_s * FS), "start_mag": float(mag) * 0.15}
    else:
        state["precursor"] = None
    state["last_event_time"] = now()
    state["scheduled_next"] = None

# ----------------- SENSOR SIGNAL GENERATORS -----------------
def _baseline_samples(n=1):
    """Return baseline noise sample(s) for accel, geo, seis as tuple arrays."""
    # small gaussian + pink-ish noise for longer sequences (we only need n=1 for streaming)
    if n == 1:
        # single-sample approximations
        accel_n = np.random.normal(0, 0.02) + 0.02 * (random.random()-0.5)
        geo_n   = np.random.normal(0, 0.04) + 0.02 * (random.random()-0.5)
        seis_n  = np.random.normal(0, 0.01) + 0.01 * (random.random()-0.5)
        return float(accel_n * state['noise_level']), float(geo_n * state['noise_level']), float(seis_n * state['noise_level'])
    else:
        pn = pink_noise(n)
        # scale pink for each sensor differently
        return (0.02 * np.random.randn(n) + 0.05 * pn,
                0.04 * np.random.randn(n) + 0.03 * pn,
                0.01 * np.random.randn(n) + 0.02 * pn)

def _machinery_interference(tick):
    """Occasional narrowband sinusoid to mimic machine noise (low amplitude)."""
    if random.random() < MACHINERY_PROB:
        f = random.uniform(6, 30)
        amp = random.uniform(0.01, 0.06)
        val = amp * math.sin(2 * math.pi * f * tick / FS)
        return val
    return 0.0

def _apply_event_waveform(tick, event):
    """Compute waveform contribution at the current tick for an event object."""
    # event dict: remaining, magnitude, phase, freq
    # compute how long since event started using remaining & magnitude (approx)
    # For simplicity, we use remaining as a proxy and compute t_rel
    # t_rel increases as event proceeds
    if event is None:
        return 0.0
    total_ticks = int(round(event['remaining']))  # not precise but okay for streaming
    # We don't track elapsed easily here; instead use phase & freq + remaining as decaying parameter
    decay_progress = (event['remaining'] / max(1.0, total_ticks))
    # Use a decaying sinusoid (note: as remaining decreases, decay reduces amplitude)
    # To get a forward-progressing wave, use global t
    t = state['t'] * (1.0 / FS)
    amp = event['magnitude'] * math.exp(-1.2 * (max(0, (total_ticks - event['remaining'])/FS)))
    value = amp * math.sin(2 * math.pi * event['freq'] * t + event['phase']) * math.exp(-0.08 * (total_ticks - event['remaining']))
    return float(value)

# ----------------- MAIN READINGS API -----------------
def step():
    """Advance time and handle scheduled events; to be called every sample tick."""
    state['t'] += 1
    # Check scheduled events
    if state["scheduled_next"] is None:
        _schedule_next_event()
    _maybe_start_scheduled()
    # progress precursor if present (precursor acts before full event)
    if state.get("precursor"):
        # precursor countdown reduces until 0, then main event remains (already set)
        state["precursor"]["remaining"] -= 1
        if state["precursor"]["remaining"] <= 0:
            state["precursor"] = None
    # progress main event
    if state.get("event"):
        state["event"]["remaining"] -= 1
        if state["event"]["remaining"] <= 0:
            # clear event and set cooldown timestamp
            state["event"] = None
            state["last_event_time"] = now()

def get_readings():
    """
    Return a dict with accelerometer, geophone, seismometer and label (0/1).
    Call this at approx FS times per second (or in your backend loop).
    """
    # state advances
    step()
    # baseline noises
    acc_b, geo_b, seis_b = _baseline_samples(1)
    # optional interference
    mach = _machinery_interference(state['t'])
    acc = acc_b + mach
    geo = geo_b + mach * 0.6
    seis = seis_b + mach * 0.25

    # precursor contribution (gentle ramp)
    if state.get("precursor"):
        # ramp amplitude proportional to remaining precursor ticks
        pre = state["precursor"]
        pre_progress = max(0.0, pre["remaining"]) / max(1.0, int(PRECURSOR_MAX_S * FS))
        pre_amp = pre["start_mag"] * (1.0 - pre_progress)
        # low-frequency wobble
        acc += pre_amp * math.sin(2 * math.pi * 1.5 * state['t'] / FS)
        geo += pre_amp * 0.8 * math.sin(2 * math.pi * 1.0 * state['t'] / FS)
        seis += pre_amp * 0.4 * math.sin(2 * math.pi * 0.8 * state['t'] / FS)

    # event waveform contribution
    if state.get("event"):
        ev = state["event"]
        # compute waveform once
        base_wave = _apply_event_waveform(state['t'], ev)
        # sensor-specific scaling & slight phase/jitter
        acc += base_wave * 1.0
        geo += base_wave * 1.6
        seis += base_wave * 0.45

    # small clipping to realistic demo ranges
    acc = float(np.clip(acc, -10.0, 10.0))
    geo = float(np.clip(geo, -20.0, 20.0))
    seis = float(np.clip(seis, -5.0, 5.0))

    label = 1 if (state.get("event") or state.get("precursor")) else 0
    timestamp = now().isoformat()

    return {
        "timestamp": timestamp,
        "accelerometer": round(acc, 4),
        "geophone": round(geo, 4),
        "seismometer": round(seis, 4),
        "label": int(label)
    }

def is_event_active():
    return True if (state.get("event") or state.get("precursor")) else False

# ----------------- QUICK DEMO LOOP -----------------
if __name__ == "__main__":
    import time
    print("Seismic demo streaming (Ctrl+C to stop). Use trigger_event(...) to force an event.")
    # ensure schedule exists
    _schedule_next_event()
    try:
        while True:
            r = get_readings()
            print(f"{r['timestamp']} | acc={r['accelerometer']} geo={r['geophone']} seis={r['seismometer']} label={r['label']}")
            time.sleep(1.0/FS)
    except KeyboardInterrupt:
        print("Stopped demo.")
