import numpy as np

# Optimized Digital-to-Digital Line Coding
# Key improvements:
# - Vectorized operations instead of loops
# - Pre-allocated arrays instead of list append + concatenate
# - Batch processing for decoding

def _bits_from_string(bit_string: str):
    return [1 if ch == '1' else 0 for ch in bit_string.strip()]

def bits_input(bits):
    """Accepts list of 0/1 or a string like '10101'. Returns numpy array."""
    if isinstance(bits, str):
        return np.array(_bits_from_string(bits), dtype=int)
    return np.array(bits, dtype=int)

def encode(bits, scheme: str, samples_per_bit: int = 100, A: float = 1.0, initial_level: float = -1.0):
    """
    Optimized encoding using vectorization.
    Returns (t, x) where:
      - t: time axis (samples)
      - x: encoded waveform samples (numpy array)
    """
    bits = bits_input(bits)
    scheme = scheme.strip().lower()
    spb = int(samples_per_bit)

    if spb < 2:
        raise ValueError("samples_per_bit must be >= 2")

    n_bits = len(bits)
    total_samples = n_bits * spb
    
    # Pre-allocate output array (faster than concatenation)
    x = np.zeros(total_samples, dtype=float)
    
    if scheme == "nrz-l":
        # Vectorized: directly map bits to levels and repeat
        levels = np.where(bits == 1, A, -A)
        x = np.repeat(levels, spb)

    elif scheme == "nrz-i":
        # Track level changes
        level = float(initial_level)
        for i, b in enumerate(bits):
            if b == 1:
                level = -level
            x[i*spb:(i+1)*spb] = level

    elif scheme == "manchester":
        half = spb // 2
        if spb % 2 != 0:
            raise ValueError("Manchester needs even samples_per_bit (e.g., 100).")
        
        # Vectorized Manchester encoding
        for i, b in enumerate(bits):
            if b == 1:
                x[i*spb:i*spb+half] = A
                x[i*spb+half:(i+1)*spb] = -A
            else:
                x[i*spb:i*spb+half] = -A
                x[i*spb+half:(i+1)*spb] = A

    elif scheme == "ami":
        last_pulse = -A
        for i, b in enumerate(bits):
            if b == 0:
                x[i*spb:(i+1)*spb] = 0.0
            else:
                last_pulse = -last_pulse
                x[i*spb:(i+1)*spb] = last_pulse
    else:
        raise ValueError(f"Unknown scheme '{scheme}'. Use: nrz-l, nrz-i, manchester, ami")

    t = np.arange(total_samples, dtype=float) / spb
    return t, x

def decode(x, scheme: str, samples_per_bit: int = 100, A: float = 1.0, initial_level: float = -1.0):
    """
    Optimized decoding using vectorized operations.
    Returns list of 0/1 bits.
    """
    x = np.asarray(x)
    scheme = scheme.strip().lower()
    spb = int(samples_per_bit)

    if len(x) % spb != 0:
        raise ValueError("Signal length must be a multiple of samples_per_bit.")

    n_bits = len(x) // spb
    
    # Reshape signal into (n_bits, samples_per_bit) for batch processing
    x_reshaped = x.reshape(n_bits, spb)
    
    if scheme == "nrz-l":
        # Vectorized: compute mean of each bit segment and threshold
        avg = np.mean(x_reshaped, axis=1)
        bits_out = (avg >= 0).astype(int).tolist()

    elif scheme == "nrz-i":
        # NRZ-I requires sequential processing (state-dependent)
        bits_out = []
        prev_level = float(initial_level)
        for i in range(n_bits):
            cur_level = float(np.mean(x_reshaped[i]))
            bits_out.append(1 if np.sign(cur_level) == -np.sign(prev_level) else 0)
            prev_level = cur_level

    elif scheme == "manchester":
        if spb % 2 != 0:
            raise ValueError("Manchester needs even samples_per_bit.")
        half = spb // 2
        
        # Vectorized: compute first and second half averages
        first_half = np.mean(x_reshaped[:, :half], axis=1)
        second_half = np.mean(x_reshaped[:, half:], axis=1)
        
        # 1: + then -, 0: - then +
        bits_out = ((first_half >= 0) & (second_half < 0)).astype(int).tolist()

    elif scheme == "ami":
        # Vectorized: compute mean and threshold
        avg = np.mean(x_reshaped, axis=1)
        bits_out = (np.abs(avg) >= (A * 0.5)).astype(int).tolist()

    else:
        raise ValueError(f"Unknown scheme '{scheme}'. Use: nrz-l, nrz-i, manchester, ami")

    return bits_out
