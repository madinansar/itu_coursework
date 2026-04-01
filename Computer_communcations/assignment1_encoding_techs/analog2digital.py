import numpy as np

# ===============================
# Analog signal generator
# ===============================
def analog_signal(t, f=1.0):
    # Simple analog message signal (sine wave)
    return np.sin(2 * np.pi * f * t)

# ===============================
# Sampling
# ===============================
def sample_signal(x, fs, t):
    if fs <= 0:
        raise ValueError("fs must be > 0")

    Ts = 1.0 / fs
    t_samples = np.arange(t[0], t[-1], Ts)
    x_samples = np.interp(t_samples, t, x)
    return t_samples, x_samples

# ===============================
# Quantization
# ===============================
def quantize(x_samples, bits=3):
    """
    Uniform quantization
    bits = number of bits per sample
    """
    levels = 2 ** bits
    xmax = np.max(np.abs(x_samples))

    # Quantization step size
    delta = (2 * xmax) / levels

    # Map samples to quantization indices
    q_indices = np.floor((x_samples + xmax) / delta)
    q_indices = np.clip(q_indices, 0, levels - 1).astype(int)

    # Map indices back to quantized signal levels
    xq = -xmax + q_indices * delta + delta / 2

    return xq, q_indices

# ===============================
# Encoding
# ===============================
def encode_pcm(q_indices, bits=3):
    # Convert quantized indices (integers) into a bitstream
    if bits < 1:
        raise ValueError("bits must be >= 1")

    bitstream = []
    for q in q_indices:
        b = format(int(q), f'0{bits}b')        # binary string with leading zeros
        bitstream.extend([int(bit) for bit in b])
    return bitstream

# ===============================
# Decoding
# ===============================
def decode_pcm(bitstream, bits=3):
    # Convert the bitstream back into quantization indices
    if bits < 1:
        raise ValueError("bits must be >= 1")
    if len(bitstream) % bits != 0:
        raise ValueError("bitstream length must be a multiple of bits per sample")

    q_indices = []
    for i in range(0, len(bitstream), bits):
        b = bitstream[i:i+bits]
        q = int("".join(str(bit) for bit in b), 2)
        q_indices.append(q)

    return np.array(q_indices, dtype=int)
