import numpy as np

# ===============================
# AM Modulation
# ===============================
def am_modulate(m, t, fc=20.0, ka=0.8):
    """
    Standard AM (DSB-LC) - Vectorized
    """
    # Numpy operations are already vectorized
    carrier = np.cos(2 * np.pi * fc * t)
    s = (1 + ka * m) * carrier
    return s

# ===============================
# AM Demodulation (Envelope)
# ===============================
def am_demodulate(s, t, fc=20.0):
    """
    Envelope detection using absolute value + moving average LPF.
    Optimized for stability and clarity.
    """
    envelope = np.abs(s)

    if len(t) > 1:
        dt = t[1] - t[0]
        fs = 1.0 / dt if dt > 0 else 1.0
        # Window size covering ~5 carrier cycles
        window_size = int(5 * fs / fc)
    else:
        window_size = int(len(t) * 0.05)
    
    # Ensure window_size is at least 1
    window_size = max(1, window_size)

    # Use uniform filter (moving average)
    # np.convolve is efficient for 1D
    lpf = np.ones(window_size) / window_size
    m_rec = np.convolve(envelope, lpf, mode="same")

    # Remove DC offset
    m_rec = m_rec - np.mean(m_rec)

    # Normalize
    max_val = np.max(np.abs(m_rec))
    if max_val > 0:
        m_rec = m_rec / max_val

    return m_rec
