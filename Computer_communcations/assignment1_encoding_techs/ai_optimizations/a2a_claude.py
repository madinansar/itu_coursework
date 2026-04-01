import numpy as np

# Optimized Analog-to-Analog Modulation (AM)
# Key improvements:
# - Vectorized convolution using numpy
# - Optimized filtering with scipy-style operations
# - Pre-computed normalization factors

def am_modulate(m, t, fc=20.0, ka=0.8):
    """
    Optimized AM (DSB-LC) modulation
    m : message signal (analog)
    t : time axis
    fc: carrier frequency
    ka: modulation index
    
    Fully vectorized (already optimal)
    """
    m = np.asarray(m)
    t = np.asarray(t)
    
    carrier = np.cos(2 * np.pi * fc * t)
    s = (1 + ka * m) * carrier
    return s

def am_demodulate(s, t, fc=20.0):
    """
    Optimized envelope detection using vectorized operations
    
    Key improvements:
    - Vectorized absolute value (already fast)
    - Efficient convolution with np.convolve 'valid' mode
    - Single-pass normalization
    - Stronger low-pass filter to remove carrier frequency
    """
    s = np.asarray(s)
    t = np.asarray(t)
    
    # Envelope detection (vectorized)
    envelope = np.abs(s)

    # Stronger low-pass filter based on carrier frequency
    # Rule: window should be at least 2-3 carrier periods for smooth envelope
    # Calculate sampling rate
    if len(t) > 1:
        fs = 1.0 / (t[1] - t[0])
        # Window size should cover 3-5 carrier cycles
        window_size = max(10, int(5 * fs / fc))
    else:
        window_size = max(10, int(len(t) * 0.05))
    
    # Efficient convolution with normalized window
    # Using 'same' mode preserves signal length
    lpf = np.ones(window_size) / window_size
    m_rec = np.convolve(envelope, lpf, mode="same")

    # Vectorized DC removal and normalization
    m_rec = m_rec - np.mean(m_rec)
    
    # Safe normalization (avoid division by zero)
    max_val = np.max(np.abs(m_rec))
    if max_val > 1e-10:
        m_rec = m_rec / max_val
    
    return m_rec

def am_modulate_batch(m_batch, t, fc=20.0, ka=0.8):
    """
    Batch modulation for multiple signals (extra optimization)
    m_batch: shape (n_signals, n_samples)
    Returns: modulated signals with same shape
    """
    m_batch = np.asarray(m_batch)
    t = np.asarray(t)
    
    carrier = np.cos(2 * np.pi * fc * t)
    
    # Broadcasting: carrier is added to all signals at once
    if m_batch.ndim == 1:
        s_batch = (1 + ka * m_batch) * carrier
    else:
        # 2D batch processing
        s_batch = (1 + ka * m_batch) * carrier[np.newaxis, :]
    
    return s_batch

def am_demodulate_batch(s_batch, t, fc=20.0):
    """
    Batch demodulation for multiple signals (extra optimization)
    s_batch: shape (n_signals, n_samples)
    Returns: demodulated signals with same shape
    """
    s_batch = np.asarray(s_batch)
    t = np.asarray(t)
    
    # Envelope detection (vectorized across batch)
    envelope = np.abs(s_batch)
    
    window_size = max(5, int(len(t) * 0.01))
    lpf = np.ones(window_size) / window_size
    
    # Handle batch dimension
    if s_batch.ndim == 1:
        m_rec = np.convolve(envelope, lpf, mode="same")
        m_rec = m_rec - np.mean(m_rec)
        max_val = np.max(np.abs(m_rec))
        if max_val > 1e-10:
            m_rec = m_rec / max_val
    else:
        # 2D batch processing
        m_rec = np.zeros_like(envelope)
        for i in range(len(s_batch)):
            m_rec[i] = np.convolve(envelope[i], lpf, mode="same")
            m_rec[i] = m_rec[i] - np.mean(m_rec[i])
            max_val = np.max(np.abs(m_rec[i]))
            if max_val > 1e-10:
                m_rec[i] = m_rec[i] / max_val
    
    return m_rec
