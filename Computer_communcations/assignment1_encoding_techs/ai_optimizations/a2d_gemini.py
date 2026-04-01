import numpy as np

# ===============================
# Analog signal generator
# ===============================
def analog_signal(t, f=1.0):
    return np.sin(2 * np.pi * f * t)

# ===============================
# Sampling
# ===============================
def sample_signal(x, fs, t):
    """
    Optimized sampling using direct indexing if possible, else interp.
    """
    Ts = 1.0 / fs
    # Create sample times
    t_samples = np.arange(t[0], t[-1], Ts)
    
    # np.interp is reasonably fast, but if t is uniformly spaced we could use indexing.
    # Assuming t might not be perfectly uniform or matching fs, interp is safer.
    x_samples = np.interp(t_samples, t, x)
    return t_samples, x_samples

# ===============================
# Quantization
# ===============================
def quantize(x_samples, bits=3):
    """
    Vectorized uniform quantization.
    """
    levels = 2 ** bits
    xmax = np.max(np.abs(x_samples))
    
    if xmax == 0:
        return x_samples, np.zeros_like(x_samples, dtype=int)

    delta = (2 * xmax) / levels
    
    # Vectorized calculation
    q_indices = np.floor((x_samples + xmax) / delta)
    q_indices = np.clip(q_indices, 0, levels - 1).astype(int)

    xq = -xmax + q_indices * delta + delta / 2
    return xq, q_indices

# ===============================
# Encoding
# ===============================
def encode_pcm(q_indices, bits=3):
    """
    Highly optimized bit extraction using bitwise operations.
    Avoids string manipulation loops.
    """
    q_indices = np.asanyarray(q_indices, dtype=int)
    
    # Create a mask for powers of 2: [2^(b-1), ..., 2^0]
    # e.g. for 3 bits: [4, 2, 1]
    powers = 1 << np.arange(bits - 1, -1, -1)
    
    # Broadcasting: (N, 1) & (bits,) -> (N, bits)
    # Check if bit is set
    bit_matrix = (q_indices[:, None] & powers) > 0
    
    # Flatten to single bitstream
    return bit_matrix.astype(int).flatten().tolist()

# ===============================
# Decoding
# ===============================
def decode_pcm(bitstream, bits=3):
    """
    Highly optimized bit reconstruction using dot product.
    """
    bit_array = np.asanyarray(bitstream, dtype=int)
    
    # Reshape to (N_samples, bits)
    # Ensure length is multiple of bits
    n_samples = len(bit_array) // bits
    bit_matrix = bit_array[:n_samples*bits].reshape(n_samples, bits)
    
    # Powers of 2
    powers = 1 << np.arange(bits - 1, -1, -1)
    
    # Dot product to reconstruct integers
    q_indices = bit_matrix.dot(powers)
    
    return q_indices
