import numpy as np

def bits_input(bits):
    """
    Standardize input to a numpy array of integers (0 or 1).
    """
    if isinstance(bits, str):
        # Efficiently convert string to numpy array
        return np.fromiter((1 if c == '1' else 0 for c in bits.strip()), dtype=int)
    return np.array(bits, dtype=int)

def encode(bits, scheme: str, samples_per_bit: int = 100, A: float = 1.0, initial_level: float = -1.0):
    """
    Vectorized encoding of bits into waveform.
    """
    bits = bits_input(bits)
    scheme = scheme.strip().lower()
    spb = int(samples_per_bit)
    n_bits = len(bits)
    
    if spb < 2:
        raise ValueError("samples_per_bit must be >= 2")

    # Pre-allocate time array
    total_samples = n_bits * spb
    t = np.arange(total_samples, dtype=float) / spb

    if scheme == "nrz-l":
        # Map 0 -> -A, 1 -> +A
        # Vectorized: 2*b - 1 maps {0,1} to {-1, 1}
        levels = (2 * bits - 1) * A
        # Repeat each level spb times
        x = np.repeat(levels, spb)

    elif scheme == "nrz-i":
        # 1 causes inversion. 0 keeps state.
        # Map bits: 0 -> 1 (no change), 1 -> -1 (flip)
        changes = np.where(bits == 1, -1.0, 1.0)
        # Cumulative product determines state relative to initial
        # We need to prepend initial_level to handle the chain correctly or adjust logic
        # state[i] = initial * prod(changes[0]...changes[i])
        states = initial_level * np.cumprod(changes)
        x = np.repeat(states, spb)

    elif scheme == "manchester":
        if spb % 2 != 0:
            raise ValueError("Manchester needs even samples_per_bit.")
        
        half = spb // 2
        # Create pattern for each bit
        # 1 -> [+A, -A], 0 -> [-A, +A]
        # Shape: (n_bits, 2)
        patterns = np.empty((n_bits, 2), dtype=float)
        
        # Vectorized assignment
        mask_ones = (bits == 1)
        patterns[mask_ones, 0] = A
        patterns[mask_ones, 1] = -A
        
        patterns[~mask_ones, 0] = -A
        patterns[~mask_ones, 1] = A
        
        # Expand to full waveform
        # Repeat each column 'half' times
        # patterns is (N, 2). We want (N, 2*half) -> (N*spb,)
        # np.repeat with axis=1 repeats columns. 
        # [[A, -A], ...] -> [[A..A, -A..-A], ...]
        x = np.repeat(patterns, half, axis=1).flatten()

    elif scheme == "ami":
        # 0 -> 0V
        # 1 -> Alternating +A, -A
        levels = np.zeros(n_bits, dtype=float)
        
        # Find indices where bit is 1
        ones_indices = np.where(bits == 1)[0]
        
        if len(ones_indices) > 0:
            # Create alternating sequence [1, -1, 1, -1, ...]
            # Start with -1 so first flip becomes +1? 
            # Original code: last_pulse = -A. First 1 -> -(-A) = +A.
            # So sequence is +A, -A, +A...
            alternating_signs = np.ones(len(ones_indices))
            alternating_signs[1::2] = -1  # Flip every second one
            
            levels[ones_indices] = alternating_signs * A
            
        x = np.repeat(levels, spb)

    else:
        raise ValueError(f"Unknown scheme '{scheme}'.")

    return t, x

def decode(x, scheme: str, samples_per_bit: int = 100, A: float = 1.0, initial_level: float = -1.0):
    """
    Vectorized decoding of waveform to bits.
    """
    scheme = scheme.strip().lower()
    spb = int(samples_per_bit)

    if len(x) % spb != 0:
        raise ValueError("Signal length must be a multiple of samples_per_bit.")

    n_bits = len(x) // spb
    
    # Reshape x to (n_bits, spb) to process all bits in parallel
    x_reshaped = x.reshape(n_bits, spb)
    
    # Calculate mean of each bit segment
    means = np.mean(x_reshaped, axis=1)

    if scheme == "nrz-l":
        # Mean >= 0 -> 1, else 0
        bits_out = (means >= 0).astype(int)

    elif scheme == "nrz-i":
        # Compare current mean sign with previous mean sign
        # We need to reconstruct the levels sequence
        # Ideally, for clean signals, mean is +A or -A.
        current_signs = np.sign(means)
        
        # Prepend initial level sign
        # We need to compare sign[i] with sign[i-1]
        # But for i=0, compare with initial_level
        prev_signs = np.roll(current_signs, 1)
        prev_signs[0] = np.sign(initial_level)
        
        # If signs are different -> 1, else 0
        # sign(a) != sign(b) <=> sign(a)*sign(b) == -1
        bits_out = (current_signs * prev_signs < 0).astype(int)

    elif scheme == "manchester":
        if spb % 2 != 0:
            raise ValueError("Manchester needs even samples_per_bit.")
        half = spb // 2
        
        # Split into first half and second half
        # x_reshaped is (N, spb)
        first_halves = x_reshaped[:, :half]
        second_halves = x_reshaped[:, half:]
        
        avg1 = np.mean(first_halves, axis=1)
        avg2 = np.mean(second_halves, axis=1)
        
        # 1: + then - (avg1 > 0, avg2 < 0)
        # 0: - then + (avg1 < 0, avg2 > 0)
        
        bits_out = np.zeros(n_bits, dtype=int)
        
        # Vectorized conditions
        cond_1 = (avg1 >= 0) & (avg2 < 0)
        cond_0 = (avg1 < 0) & (avg2 >= 0)
        
        bits_out[cond_1] = 1
        bits_out[cond_0] = 0
        
        # Optional: Check for validity
        if not np.all(cond_1 | cond_0):
             # In a strict decoder we might raise error, but for vectorization speed we might skip or warn
             # Replicating original behavior:
             if np.any(~(cond_1 | cond_0)):
                 raise ValueError("Invalid Manchester segment shape.")

    elif scheme == "ami":
        # If abs(mean) > threshold -> 1, else 0
        threshold = A * 0.5
        bits_out = (np.abs(means) >= threshold).astype(int)

    else:
        raise ValueError(f"Unknown scheme '{scheme}'.")

    return bits_out.tolist()
