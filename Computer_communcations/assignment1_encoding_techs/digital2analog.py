import numpy as np

def bits_input(bits):
    if isinstance(bits, str):
        return [1 if c == '1' else 0 for c in bits.strip()]
    return [int(b) for b in bits]

def modulate(bits_str, scheme, bit_rate=1.0, fs=200.0, fc=10.0, df=None, A=1.0):
    scheme = scheme.strip().lower()
    bits = [1 if c == "1" else 0 for c in bits_str.strip()]

    Tb = 1.0 / float(bit_rate)                      # bit duration (seconds)
    spb = int(round(fs * Tb))                       # how many samples represent one bit
    if spb < 2:
        raise ValueError("fs is too small relative to bit_rate (need >=2 samples/bit).")

    # Build a time axis for the entire signal and prepare an output array
    t = np.arange(len(bits) * spb) / float(fs)
    s = np.zeros_like(t, dtype=float)

    if scheme == "ask":
        # OOK style ASK: 1 = send the carrier, 0 = send nothing
        for i, b in enumerate(bits):
            idx0 = i * spb
            idx1 = (i + 1) * spb
            if b == 1:
                s[idx0:idx1] = A * np.cos(2 * np.pi * fc * t[idx0:idx1])
            else:
                s[idx0:idx1] = 0.0

    elif scheme == "bpsk":
        # BPSK: same carrier, but phase flips by pi for bit 0
        for i, b in enumerate(bits):
            idx0 = i * spb
            idx1 = (i + 1) * spb
            phase = 0.0 if b == 1 else np.pi
            s[idx0:idx1] = A * np.cos(2 * np.pi * fc * t[idx0:idx1] + phase)

    elif scheme == "fsk":
        # FSK needs two frequencies: f0 for bit 0, f1 for bit 1
        if df is None:
            raise ValueError("FSK requires df (frequency deviation).")

        f0 = fc - df
        f1 = fc + df
        if f0 <= 0:
            raise ValueError("FSK f0 must be > 0. Choose smaller df or larger fc.")

        for i, b in enumerate(bits):
            idx0 = i * spb
            idx1 = (i + 1) * spb
            f = f1 if b == 1 else f0
            s[idx0:idx1] = A * np.cos(2 * np.pi * f * t[idx0:idx1])

    else:
        raise ValueError("Unknown scheme. Use: ask, fsk, bpsk")

    return t, s

def demodulate(t, s, scheme, bit_rate=1.0, fs=200.0, fc=10.0, df=None, A=1.0):
    scheme = scheme.strip().lower()

    Tb = 1.0 / float(bit_rate)
    spb = int(round(fs * Tb))
    if spb < 2:
        raise ValueError("fs is too small relative to bit_rate.")

    n_bits = len(s) // spb
    bits_out = []

    if scheme == "ask":
        # ASK detection: correlate with the carrier and threshold the result
        for i in range(n_bits):
            seg = s[i*spb:(i+1)*spb]
            tt = t[i*spb:(i+1)*spb]
            ref = np.cos(2*np.pi*fc*tt)
            metric = np.mean(seg * ref)             # “how much carrier energy is there?”
            # Threshold should depend on A. Nominal expected is 0.5*A for bit 1. 
            # 0.25*A is a good midpoint. We use 0.2*A to include some margin.
            bits_out.append(1 if metric > 0.2 * A else 0)

    elif scheme == "bpsk":
        # BPSK detection: correlate with carrier; sign tells the phase
        for i in range(n_bits):
            seg = s[i*spb:(i+1)*spb]
            tt = t[i*spb:(i+1)*spb]
            ref = np.cos(2*np.pi*fc*tt)
            metric = np.mean(seg * ref)
            bits_out.append(1 if metric >= 0 else 0)

    elif scheme == "fsk":
        # FSK detection: compare correlation at f0 vs f1
        if df is None:
            raise ValueError("FSK requires df (frequency deviation).")

        f0 = fc - df
        f1 = fc + df
        if f0 <= 0:
            raise ValueError("FSK f0 must be > 0. Choose smaller df or larger fc.")

        for i in range(n_bits):
            seg = s[i*spb:(i+1)*spb]
            tt = t[i*spb:(i+1)*spb]

            ref0 = np.cos(2*np.pi*f0*tt)
            ref1 = np.cos(2*np.pi*f1*tt)

            m0 = np.mean(seg * ref0)                # similarity to f0
            m1 = np.mean(seg * ref1)                # similarity to f1

            bits_out.append(1 if m1 > m0 else 0)

    else:
        raise ValueError("Unknown scheme. Use: ask, fsk, bpsk")

    return bits_out
