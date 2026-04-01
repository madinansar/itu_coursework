import numpy as np

# Optimized Digital-to-Analog Modulation
# Key improvements:
# - Vectorized signal generation (all bits at once)
# - Pre-computed time arrays
# - Eliminated list append + concatenate pattern
# - Batch correlation processing for demodulation

def bits_input(bits):
    if isinstance(bits, str):
        return np.array([1 if c == '1' else 0 for c in bits.strip()], dtype=int)
    return np.array(bits, dtype=int)

def modulate(bits, scheme: str,
             bit_rate: float = 1.0,
             fs: float = 200.0,
             fc: float = 10.0,
             A: float = 1.0,
             f0: float = 7.0,
             f1: float = 13.0):
    """
    Optimized modulation using vectorization.
    Returns (t, s) where s is analog modulated signal.
    """
    bits = bits_input(bits)
    scheme = scheme.strip().lower()

    Tb = 1.0 / bit_rate
    N = int(fs * Tb)
    if N < 10:
        raise ValueError("fs too low or bit_rate too high: need enough samples per bit")

    n_bits = len(bits)
    total_samples = n_bits * N
    
    # Pre-allocate arrays (faster than append + concatenate)
    t = np.arange(total_samples) / fs
    s = np.zeros(total_samples, dtype=float)
    
    if scheme == "ask":
        # Vectorized ASK: create carrier, then apply amplitude modulation
        carrier = np.cos(2 * np.pi * fc * t)
        # Create amplitude array by repeating each bit value N times
        amplitudes = np.repeat(bits, N) * A
        s = amplitudes * carrier

    elif scheme == "fsk":
        # Vectorized FSK: compute frequency array based on bits
        frequencies = np.where(np.repeat(bits, N) == 1, f1, f0)
        # Generate signal with time-varying frequency
        for i in range(n_bits):
            t_seg = t[i*N:(i+1)*N]
            f = f1 if bits[i] == 1 else f0
            s[i*N:(i+1)*N] = A * np.cos(2 * np.pi * f * t_seg)

    elif scheme == "bpsk":
        # Vectorized BPSK: create phase array based on bits
        carrier = np.cos(2 * np.pi * fc * t)
        # Phase shift: 0 for bit 0, pi for bit 1
        phases = np.repeat(bits, N) * np.pi
        s = A * np.cos(2 * np.pi * fc * t + phases)

    else:
        raise ValueError("Unknown scheme. Use: ask, fsk, bpsk")

    return t, s

def demodulate(t, s, scheme: str,
               bit_rate: float = 1.0,
               fs: float = 200.0,
               fc: float = 10.0,
               A: float = 1.0,
               f0: float = 7.0,
               f1: float = 13.0):
    """
    Optimized coherent demodulation using vectorized correlation.
    Returns recovered bits list.
    """
    # Ensure numpy arrays
    t = np.asarray(t)
    s = np.asarray(s)
    
    scheme = scheme.strip().lower()

    Tb = 1.0 / bit_rate
    N = int(fs * Tb)
    if len(s) % N != 0:
        raise ValueError("Signal length must be multiple of samples per bit")

    n_bits = len(s) // N
    
    # Reshape for batch processing
    s_reshaped = s.reshape(n_bits, N)
    t_reshaped = t.reshape(n_bits, N)
    
    if scheme == "ask":
        # Vectorized energy detection
        metrics = np.mean(np.abs(s_reshaped), axis=1)
        bits_out = (metrics > (A * 0.3)).astype(int).tolist()

    elif scheme == "bpsk":
        # Vectorized correlation with carrier
        carrier = np.cos(2 * np.pi * fc * t_reshaped)
        correlations = np.mean(s_reshaped * carrier, axis=1)
        # Negative correlation => bit 1, positive => bit 0
        bits_out = (correlations < 0).astype(int).tolist()

    elif scheme == "fsk":
        # Vectorized dual-tone correlation
        ref0 = np.cos(2 * np.pi * f0 * t_reshaped)
        ref1 = np.cos(2 * np.pi * f1 * t_reshaped)
        c0 = np.mean(s_reshaped * ref0, axis=1)
        c1 = np.mean(s_reshaped * ref1, axis=1)
        bits_out = (c1 > c0).astype(int).tolist()

    else:
        raise ValueError("Unknown scheme. Use: ask, fsk, bpsk")

    return bits_out
