import numpy as np

# ===============================
# AM Modulation (DSB-LC)
# ===============================
def am_modulate(m, t, fc=20.0, ka=0.8):
    carrier = np.cos(2 * np.pi * fc * t)
    s = (1.0 + ka * m) * carrier
    return s

# ===============================
# AM Demodulation (envelope detector)
# ===============================
def am_demodulate(s, t, fc=20.0):
    # Envelope detection step (rectify)
    envelope = np.abs(s)

    # Estimate sampling rate from time axis
    if len(t) < 2:
        raise ValueError("Time vector t must contain at least 2 samples.")

    dt = t[1] - t[0]
    if dt <= 0:
        raise ValueError("Time vector t must be increasing.")
    fs = 1.0 / dt

    # Moving-average low-pass filter:
    # Make the window cover a few carrier cycles to smooth out carrier ripples.
    # 5 cycles is usually enough.
    window_size = int(5 * fs / fc)

    # Keep it within reasonable bounds
    window_size = max(10, window_size)                 # not too small
    window_size = min(window_size, len(envelope) // 2) # not too big for short signals

    # Build simple LPF kernel
    lpf = np.ones(window_size, dtype=float) / window_size
    m_rec = np.convolve(envelope, lpf, mode="same")

    # Remove DC (AM envelope has a big DC component from the "+1")
    m_rec = m_rec - np.mean(m_rec)

    # Normalize safely (avoid dividing by zero)
    peak = np.max(np.abs(m_rec))
    if peak > 1e-12:
        m_rec = m_rec / peak

    return m_rec
# -------------------------
# PM Modulation
# -------------------------
def pm_modulate(m, t, fc=20.0, kp=1.0):
    """
    Phase Modulation (PM)
    s(t) = cos(2π f_c t + k_p * m(t))
    kp: phase sensitivity (radians per unit amplitude of m)
    """
    return np.cos(2 * np.pi * fc * t + kp * m)

# -------------------------
# FM Modulation
# -------------------------
def fm_modulate(m, t, fc=20.0, kf=5.0):
    """
    Frequency Modulation (FM)
    s(t) = cos(2π f_c t + 2π k_f ∫ m(τ) dτ)
    kf: frequency sensitivity (Hz per unit amplitude of m)
    """
    dt = t[1] - t[0]
    integral_m = np.cumsum(m) * dt
    phase = 2 * np.pi * fc * t + 2 * np.pi * kf * integral_m
    return np.cos(phase)

# -------------------------
# Shared helper: I/Q demod (used by PM and FM)
# -------------------------
def _lowpass_moving_avg(x, window_size):
    """
    Simple low-pass filter using moving average.
    """
    window_size = max(3, int(window_size))
    kernel = np.ones(window_size) / window_size
    return np.convolve(x, kernel, mode="same")

def _iq_baseband(s, t, fc, lpf_cycles=5):
    """
    Coherent downconversion to baseband I/Q using cos/sin mixing + moving-average LPF.
    Returns I, Q (low-pass filtered).
    """
    dt = t[1] - t[0]
    fs = 1.0 / dt

    # Mix down
    i_raw = 2.0 * s * np.cos(2 * np.pi * fc * t)
    q_raw = -2.0 * s * np.sin(2 * np.pi * fc * t)

    # Low-pass window: cover a few carrier cycles
    # window_size ~ (cycles / fc) seconds -> samples = fs * cycles/fc
    window_size = int(fs * (lpf_cycles / fc))
    window_size = max(15, window_size)

    I = _lowpass_moving_avg(i_raw, window_size)
    Q = _lowpass_moving_avg(q_raw, window_size)
    return I, Q

# -------------------------
# PM Demodulation
# -------------------------
def pm_demodulate(s, t, fc=20.0, kp=1.0):
    """
    Recover m(t) from PM by estimating instantaneous phase:
      phase = unwrap(arctan2(Q, I))
      m_rec ~ phase / kp
    """
    I, Q = _iq_baseband(s, t, fc)
    phase = np.unwrap(np.arctan2(Q, I))

    # Remove carrier term (approx). After mixing, carrier is mostly removed,
    # but phase still has an arbitrary constant offset.
    phase = phase - np.mean(phase)

    m_rec = phase / kp
    # normalize for nicer plotting
    if np.max(np.abs(m_rec)) > 0:
        m_rec = m_rec / np.max(np.abs(m_rec))
    return m_rec

# -------------------------
# FM Demodulation
# -------------------------
def fm_demodulate(s, t, fc=20.0, kf=5.0):
    """
    FM demodulation (frequency discriminator) using IQ baseband + phase derivative.

    Idea:
      1) Mix the FM signal down to baseband (I/Q)
      2) Get instantaneous phase: phase = unwrap(arctan2(Q, I))
      3) Differentiate phase to get instantaneous frequency
      4) The remaining frequency deviation ~ kf * m(t)  =>  m(t) ≈ inst_freq / kf
      5) Low-pass filter + remove DC + normalize for clean plotting
    """

    # Bring the signal to baseband
    I, Q = _iq_baseband(s, t, fc)

    # Instantaneous phase of complex baseband signal
    phase = np.unwrap(np.arctan2(Q, I))

    # Differentiate phase
    dt = t[1] - t[0]
    dphase = np.diff(phase)

    dphase = (dphase + np.pi) % (2 * np.pi) - np.pi

    inst_freq = (1.0 / (2 * np.pi)) * (dphase / dt)

    # Match lengths
    inst_freq = np.concatenate([inst_freq, [inst_freq[-1]]])

    # Convert frequency deviation to message amplitude
    if kf == 0:
        raise ValueError("kf must be non-zero for FM demodulation.")
    m_rec = inst_freq / float(kf)

    # Remove DC offset
    m_rec = m_rec - np.mean(m_rec)

    # Low-pass to remove leftover ripple/high-frequency junk
    fs = 1.0 / dt
    win = max(5, int(0.08 * fs))  # ~20 ms window
    m_rec = _lowpass_moving_avg(m_rec, win)
    m_rec = _lowpass_moving_avg(m_rec, win)

    # Normalize safely (avoid dividing by zero)
    peak = np.max(np.abs(m_rec))
    if peak > 1e-12:
        m_rec = m_rec / peak

    return m_rec
