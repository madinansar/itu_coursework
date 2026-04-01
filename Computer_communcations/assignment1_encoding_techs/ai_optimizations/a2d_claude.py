import numpy as np

# Optimized Analog-to-Digital Conversion (PCM)
# Key improvements:
# - Vectorized quantization (no loops)
# - Optimized bit packing/unpacking using numpy operations
# - Eliminated Python loops where possible

def analog_signal(t, f=1.0):
    """
    Example analog signal: sine wave
    Fully vectorized (already optimal)
    """
    return np.sin(2 * np.pi * f * t)

def sample_signal(x, fs, t):
    """
    Sample analog signal x(t) at sampling frequency fs
    Already vectorized using np.interp
    """
    Ts = 1 / fs
    t_samples = np.arange(t[0], t[-1], Ts)
    x_samples = np.interp(t_samples, t, x)
    return t_samples, x_samples

def quantize(x_samples, bits=3):
    """
    Optimized uniform quantization using vectorized operations
    """
    x_samples = np.asarray(x_samples)
    levels = 2 ** bits
    xmax = np.max(np.abs(x_samples))
    
    if xmax == 0:
        # Handle zero signal case
        return np.zeros_like(x_samples), np.zeros(len(x_samples), dtype=int)
    
    delta = (2 * xmax) / levels
    
    # Vectorized quantization (no loops)
    q_indices = np.floor((x_samples + xmax) / delta).astype(int)
    q_indices = np.clip(q_indices, 0, levels - 1)

    # Vectorized reconstruction
    xq = -xmax + q_indices * delta + delta / 2
    
    return xq, q_indices

def encode_pcm(q_indices, bits=3):
    """
    Optimized PCM encoding using numpy bit operations
    Converts quantized indices to binary bitstream
    """
    q_indices = np.asarray(q_indices, dtype=int)
    
    # Vectorized bit extraction
    # Create array of bit positions
    bit_positions = np.arange(bits - 1, -1, -1)
    
    # Extract all bits at once using broadcasting
    # Shape: (len(q_indices), bits)
    bits_array = (q_indices[:, np.newaxis] >> bit_positions) & 1
    
    # Flatten to 1D bitstream
    bitstream = bits_array.flatten().tolist()
    
    return bitstream

def decode_pcm(bitstream, bits=3):
    """
    Optimized PCM decoding using vectorized operations
    Converts bitstream back to quantized indices
    """
    bitstream = np.asarray(bitstream, dtype=int)
    
    # Ensure bitstream length is multiple of bits
    n_symbols = len(bitstream) // bits
    bitstream_trimmed = bitstream[:n_symbols * bits]
    
    # Reshape into (n_symbols, bits)
    bits_reshaped = bitstream_trimmed.reshape(n_symbols, bits)
    
    # Vectorized conversion to integers
    # Each row represents a binary number
    bit_weights = 2 ** np.arange(bits - 1, -1, -1)
    q_indices = np.sum(bits_reshaped * bit_weights, axis=1)
    
    return q_indices
