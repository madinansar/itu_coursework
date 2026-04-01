import numpy as np

def _bits_from_string(bit_string: str):
    return [1 if ch == '1' else 0 for ch in bit_string.strip()]

def bits_input(bits):
    if isinstance(bits, str):
        return _bits_from_string(bits)
    return [int(b) for b in bits]

def encode(bits, scheme: str, samples_per_bit: int = 100, A: float = 1.0, initial_level: float = -1.0):
    """
    Encode bits into a waveform.

    Returns:
      t: time values measured in "bit units" (0 to number_of_bits)
      x: waveform samples (one long array)

    samples_per_bit (spb):
      how many samples we use to draw one bit (more samples => smoother plot)
    """
    bits = bits_input(bits)              # make sure bits are [0/1] list
    scheme = scheme.strip().lower()      # normalize name: "NRZ-L" -> "nrz-l"
    spb = int(samples_per_bit)           # ensure integer

    if spb < 2:
        raise ValueError("samples_per_bit must be >= 2")  # need at least 2 points per bit

    x_parts = []  # we build each bit segment separately, then join them at the end

    if scheme == "nrz-l":
        # For each bit, just output a constant level for the whole bit time
        for b in bits:
            level = +A if b == 1 else -A
            x_parts.append(np.full(spb, level, dtype=float))

    elif scheme == "nrz-i":
        # Start from an initial level, then flip when you see a '1'
        level = float(initial_level)
        for b in bits:
            if b == 1:
                level = -level           # '1' means invert at start of bit
            x_parts.append(np.full(spb, level, dtype=float))

    elif scheme == "manchester":
        # Manchester splits each bit into two halves: first half then second half
        if spb % 2 != 0:
            raise ValueError("Manchester needs even samples_per_bit (e.g., 100).")

        half = spb // 2
        for b in bits:
            # 1 -> high then low, 0 -> low then high
            if b == 1:
                first, second = +A, -A
            else:
                first, second = -A, +A

            x_parts.append(np.concatenate([
                np.full(half, first, dtype=float),
                np.full(half, second, dtype=float)
            ]))

    elif scheme == "ami":
        # AMI alternates the polarity (+A, -A, +A, ...) for successive '1's
        last_pulse = -A  # set so the first '1' becomes +A after flipping
        for b in bits:
            if b == 0:
                x_parts.append(np.zeros(spb, dtype=float))  # '0' is 0V
            else:
                last_pulse = -last_pulse                    # flip polarity each time we see a '1'
                x_parts.append(np.full(spb, last_pulse, dtype=float))

    else:
        raise ValueError(f"Unknown scheme '{scheme}'. Use: nrz-l, nrz-i, manchester, ami")

    # Join all bit segments into one long waveform
    x = np.concatenate(x_parts) if x_parts else np.array([], dtype=float)

    # Time axis in "bit units": one bit is 1.0 time unit
    t = np.arange(len(x), dtype=float) / spb
    return t, x

def decode(x, scheme: str, samples_per_bit: int = 100, A: float = 1.0, initial_level: float = -1.0):
    """
    Decode a waveform back into bits.
    Assumes ideal/noiseless waveform made by our encoder.

    x must have length multiple of samples_per_bit (each bit = spb samples).
    """
    scheme = scheme.strip().lower()
    spb = int(samples_per_bit)

    if len(x) % spb != 0:
        raise ValueError("Signal length must be a multiple of samples_per_bit.")

    n_bits = len(x) // spb
    bits_out = []

    if scheme == "nrz-l":
        # Decide each bit by the sign of the average level in its segment
        for i in range(n_bits):
            seg = x[i*spb:(i+1)*spb]
            avg = float(np.mean(seg))
            bits_out.append(1 if avg >= 0 else 0)

    elif scheme == "nrz-i":
        # A '1' means there was an inversion at the bit boundary
        prev_level = float(initial_level)
        for i in range(n_bits):
            seg = x[i*spb:(i+1)*spb]
            cur_level = float(np.mean(seg))

            # If cur_level has opposite sign of prev_level => inversion => bit = 1
            bits_out.append(1 if np.sign(cur_level) == -np.sign(prev_level) else 0)

            # Update for next comparison
            prev_level = cur_level

    elif scheme == "manchester":
        # Split each bit into 2 halves and look at the sign pattern
        if spb % 2 != 0:
            raise ValueError("Manchester needs even samples_per_bit.")

        half = spb // 2
        for i in range(n_bits):
            seg = x[i*spb:(i+1)*spb]
            first_avg = float(np.mean(seg[:half]))
            second_avg = float(np.mean(seg[half:]))

            # 1: + then -, 0: - then +
            if first_avg >= 0 and second_avg < 0:
                bits_out.append(1)
            elif first_avg < 0 and second_avg >= 0:
                bits_out.append(0)
            else:
                # If it doesn't match either pattern, waveform is not a valid clean Manchester bit
                raise ValueError("Invalid Manchester segment shape (not a clean mid-bit transition).")

    elif scheme == "ami":
        # For AMI, a bit is 1 if the segment is far from 0, else it's 0
        for i in range(n_bits):
            seg = x[i*spb:(i+1)*spb]
            avg = float(np.mean(seg))
            bits_out.append(0 if abs(avg) < (A * 0.5) else 1)

    else:
        raise ValueError(f"Unknown scheme '{scheme}'. Use: nrz-l, nrz-i, manchester, ami")

    return bits_out