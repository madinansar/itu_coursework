import numpy as np

def bits_input(bits):
    if isinstance(bits, str):
        return np.fromiter((1 if c == '1' else 0 for c in bits.strip()), dtype=int)
    return np.array(bits, dtype=int)

def modulate(bits, scheme: str,
             bit_rate: float = 1.0,
             fs: float = 200.0,
             fc: float = 10.0,
             A: float = 1.0,
             f0: float = 7.0,
             f1: float = 13.0):
    """
    Vectorized modulation.
    """
    bits = bits_input(bits)
    scheme = scheme.strip().lower()

    Tb = 1.0 / bit_rate
    N = int(fs * Tb)
    if N < 10:
        raise ValueError("fs too low or bit_rate too high")

    n_bits = len(bits)
    total_samples = n_bits * N
    
    # Generate global time axis
    # t goes from 0 to n_bits*Tb
    t = np.arange(total_samples, dtype=float) / fs
    
    # Expand bits to match sample rate
    # (n_bits,) -> (n_bits * N,)
    bits_expanded = np.repeat(bits, N)

    if scheme == "ask":
        # Amplitude is A where bit is 1, else 0
        amplitude = np.where(bits_expanded == 1, A, 0.0)
        s = amplitude * np.cos(2 * np.pi * fc * t)

    elif scheme == "fsk":
        # Frequency is f1 where bit is 1, else f0
        freq = np.where(bits_expanded == 1, f1, f0)
        s = A * np.cos(2 * np.pi * freq * t)

    elif scheme == "bpsk":
        # Phase is pi where bit is 1, else 0
        phase = np.where(bits_expanded == 1, np.pi, 0.0)
        s = A * np.cos(2 * np.pi * fc * t + phase)

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
    Vectorized coherent demodulation.
    """
    t = np.asanyarray(t)
    s = np.asanyarray(s)
    scheme = scheme.strip().lower()

    Tb = 1.0 / bit_rate
    N = int(fs * Tb)
    
    if len(s) % N != 0:
        # Handle potential floating point rounding issues in length if necessary, 
        # but strictly following original logic:
        raise ValueError("Signal length must be multiple of samples per bit")

    n_bits = len(s) // N
    
    # Reshape to (n_bits, N) to process bits in parallel
    s_reshaped = s.reshape(n_bits, N)
    t_reshaped = t.reshape(n_bits, N)

    if scheme == "ask":
        # Metric: mean of absolute value
        metrics = np.mean(np.abs(s_reshaped), axis=1)
        bits_out = (metrics > (A * 0.3)).astype(int)

    elif scheme == "bpsk":
        # Correlate with carrier
        ref = np.cos(2 * np.pi * fc * t_reshaped)
        corr = np.mean(s_reshaped * ref, axis=1)
        # corr < 0 means phase shift pi (bit 1), corr > 0 means phase 0 (bit 0)
        bits_out = (corr < 0).astype(int)

    elif scheme == "fsk":
        # Correlate with f0 and f1
        ref0 = np.cos(2 * np.pi * f0 * t_reshaped)
        ref1 = np.cos(2 * np.pi * f1 * t_reshaped)
        
        c0 = np.mean(s_reshaped * ref0, axis=1)
        c1 = np.mean(s_reshaped * ref1, axis=1)
        
        bits_out = (c1 > c0).astype(int)

    else:
        raise ValueError("Unknown scheme. Use: ask, fsk, bpsk")

    return bits_out.tolist()
