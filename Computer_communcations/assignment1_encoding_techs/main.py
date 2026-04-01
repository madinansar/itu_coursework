import matplotlib.pyplot as plt

from ui import ask_choice, ask_bits, ask_int, ask_float

from digital2digital import encode, decode
from digital2analog import modulate, demodulate
from analog2digital import analog_signal, sample_signal, quantize, encode_pcm, decode_pcm
from analog2analog import  am_modulate, am_demodulate, pm_modulate, pm_demodulate, fm_modulate, fm_demodulate
import time
def benchmark(func, runs=10):
    start = time.perf_counter()
    for _ in range(runs):
        func()
    end = time.perf_counter()
    return (end - start) / runs

# -------------------------
# Helpers for plotting
# -------------------------
def plot_digital(t, x, bits, title):
    plt.figure()
    plt.plot(t, x)
    plt.title(title)
    plt.xlabel("Time (bit periods)")
    plt.ylabel("Amplitude")

    for k in range(len(bits) + 1):
        plt.axvline(k, linewidth=0.8)

    for i, b in enumerate(bits):
        plt.text(i + 0.05, 1.1, str(b))

    plt.ylim(-1.5, 1.5)
    plt.grid(True)
    plt.tight_layout()


def plot_analog(t, s, title):
    plt.figure()
    plt.plot(t, s)
    plt.title(title)
    plt.xlabel("Time (seconds)")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.tight_layout()

# -------------------------
# Section 1: Digital -> Digital
# -------------------------
def run_section1():
    bits_str = ask_bits()

    # Internal simulation setting (not needed for user input)
    spb = 100  # samples per bit (used only for drawing/decoding)
    
    scheme = ask_choice(
        "Section 1: Choose line coding scheme",
        [("1", "NRZ-L"), ("2", "NRZ-I"), ("3", "Manchester"), ("4", "AMI")]
    )

    scheme_map = {"1": "nrz-l", "2": "nrz-i", "3": "manchester", "4": "ami"}
    scheme_name = scheme_map[scheme]

    # Manchester needs an even number of samples so the bit can be split into two equal halves
    if scheme_name == "manchester" and (spb % 2 != 0):
        spb += 1  # auto-fix if needed (keeps interface simple)

    bits = [int(c) for c in bits_str]

    # Encode and decode once (main result)
    t, x = encode(bits_str, scheme_name, samples_per_bit=spb)
    decoded_bits = decode(x, scheme_name, samples_per_bit=spb)

    print("\n===== RESULT (Section 1: Digital -> Digital) =====")
    print(f"Scheme: {scheme_name}")
    print(f"Input bits:   {bits}")
    print(f"Output bits:  {decoded_bits}")

    # Optional: clean verification message 
    if decoded_bits != bits:
        print("Warning: decoded bits differ from input bits (check parameters).")

    # ---- Benchmark (Section 1): encoding + decoding ----
    avg_enc = benchmark(lambda: encode(bits_str, scheme_name, samples_per_bit=spb), runs=50)
    avg_dec = benchmark(lambda: decode(x, scheme_name, samples_per_bit=spb), runs=50)
    print(f"[Benchmark S1] encode avg: {avg_enc:.6f}s | decode avg: {avg_dec:.6f}s")

    plot_digital(t, x, bits, f"{scheme_name} encoding (Section 1)")
    plt.show()

# -------------------------
# Section 2: Digital -> Analog
# -------------------------
def run_section2():
    # Bits are the digital message we will modulate on a carrier
    bits_str = ask_bits("Enter bit string (only 0/1): ")

    # These two parameters define timing and carrier shape
    bit_rate = ask_float("Bit rate Rb (bits/s): ")
    fc = ask_float("Carrier frequency fc (Hz): ")

    # Choose modulation type
    scheme = ask_choice(
        "Section 2: Choose modulation scheme",
        [("1", "ASK (OOK)"), ("2", "FSK"), ("3", "BPSK")]
    )
    scheme_map = {"1": "ask", "2": "fsk", "3": "bpsk"}
    scheme_name = scheme_map[scheme]

    # For FSK, we need how far the two frequencies are separated
    df = None
    if scheme_name == "fsk":
        df = ask_float("FSK frequency deviation Δf (Hz): ")
        # Simple validity check (too small separation can cause bad demodulation)
        if df < (bit_rate / 2):
            print("Note: Δf is quite small. Consider using Δf >= Rb/2 for clearer separation.")

    # Sampling frequency must be high enough to represent the carrier AND the bit transitions
    # Rule of thumb: fs >= 20*fc and fs >= 10*Rb
    fs = max(20.0 * fc, 10.0 * bit_rate)

    # Modulate and demodulate
    # If your modulate/demodulate functions do not support df, see the NOTE below.
    if scheme_name == "fsk":
        t, s = modulate(bits_str, scheme_name, bit_rate=bit_rate, fs=fs, fc=fc, df=df)
        recovered = demodulate(t, s, scheme_name, bit_rate=bit_rate, fs=fs, fc=fc, df=df)
    else:
        t, s = modulate(bits_str, scheme_name, bit_rate=bit_rate, fs=fs, fc=fc)
        recovered = demodulate(t, s, scheme_name, bit_rate=bit_rate, fs=fs, fc=fc)

    bits = [int(c) for c in bits_str]

    print("\n===== RESULT (Section 2: Digital -> Analog) =====")
    print(f"Scheme: {scheme_name.upper()}")
    print(f"Parameters used: Rb={bit_rate} bps, fc={fc} Hz, fs={fs:.2f} Hz")
    if scheme_name == "fsk":
        print(f"FSK deviation: Δf={df} Hz")

    print(f"Input bits:     {bits}")
    print(f"Recovered bits: {recovered}")

    # Only show a warning if something is wrong
    if recovered != bits:
        print("Warning: recovered bits differ from input bits.")

    # ---- Benchmark (Section 2): modulation + demodulation ----
    if scheme_name == "fsk":
        avg_mod = benchmark(lambda: modulate(bits_str, scheme_name, bit_rate=bit_rate, fs=fs, fc=fc, df=df), runs=30)
        avg_dem = benchmark(lambda: demodulate(t, s, scheme_name, bit_rate=bit_rate, fs=fs, fc=fc, df=df), runs=30)
    else:
        avg_mod = benchmark(lambda: modulate(bits_str, scheme_name, bit_rate=bit_rate, fs=fs, fc=fc), runs=30)
        avg_dem = benchmark(lambda: demodulate(t, s, scheme_name, bit_rate=bit_rate, fs=fs, fc=fc), runs=30)

    print(f"[Benchmark S2] mod avg: {avg_mod:.6f}s | demod avg: {avg_dem:.6f}s")

    # Plot the modulated analog waveform
    plot_analog(t, s, f"{scheme_name.upper()} modulated signal (Section 2)")
    plt.show()


# -------------------------
# Section 3: Analog -> Digital (PCM)  + WAV option
# -------------------------
def run_section3():
    import numpy as np

    # Choose input source
    mode = ask_choice(
        "Section 3 input source",
        [("1", "Synthetic sine wave"), ("2", "WAV audio file (.wav)")]
    )

    # -------------- Mode 1: Sine wave --------------
    if mode == "1":
        fm = ask_float("Message frequency fm (Hz): ")
        fs = ask_float("Sampling frequency fs (Hz): ")
        q_bits = ask_int("Quantization bits per sample: ")

        if fm <= 0:
            print("fm must be > 0.")
            return
        if fs <= 0:
            print("fs must be > 0.")
            return
        if q_bits <= 0:
            print("Quantization bits must be > 0.")
            return

        # Nyquist warning
        if fs < 2 * fm:
            print("Warning: fs < 2*fm (Nyquist). Expect aliasing.")

        # "Analog" smooth reference for plotting
        t = np.linspace(0, 1, 5000)
        x = analog_signal(t, f=fm)

        # Sample using your existing sampler
        ts, xs = sample_signal(x, fs, t)

        # For this sine, full-scale is close to 1, but we keep it consistent with quantize()
        # Your quantize() currently uses xmax = max(abs(xs)) internally.
        xq, q_idx = quantize(xs, bits=q_bits)

        # Encode -> decode
        bitstream = encode_pcm(q_idx, bits=q_bits)
        q_rec = decode_pcm(bitstream, bits=q_bits)

        # Reconstruct using the SAME scaling as the quantizer used
        xmax = np.max(np.abs(xs))
        levels = 2 ** q_bits
        delta = (2 * xmax) / levels
        x_rec = -xmax + q_rec * delta + (delta / 2)

        out_fs = None  # no output wav for sine mode

    # -------------- Mode 2: WAV audio --------------
    else:
        wav_name = input("WAV filename (example: voice.wav): ").strip()
        if not wav_name.lower().endswith(".wav"):
            print("Please provide a .wav file name.")
            return

        q_bits = ask_int("Quantization bits per sample (recommended 8 to 12): ")
        if q_bits <= 0:
            print("Quantization bits must be > 0.")
            return

        # Limit duration so the bitstream doesn't become huge
        max_seconds = ask_float("Max seconds to process (example 2 or 3): ")
        if max_seconds <= 0:
            print("Max seconds must be > 0.")
            return

        # Read WAV using built-in wave module (no installs)
        import wave
        try:
            with wave.open(wav_name, "rb") as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                fs = wf.getframerate()
                n_frames = wf.getnframes()

                # Read only the first max_seconds
                frames_to_read = int(min(n_frames, max_seconds * fs))
                raw = wf.readframes(frames_to_read)
        except FileNotFoundError:
            print("File not found. Put the WAV in the same folder as main.py or write full path.")
            return
        except wave.Error as e:
            print(f"Could not read WAV file: {e}")
            return

        # Convert raw bytes to numpy samples
        # Handle common PCM formats: 8-bit unsigned, 16-bit signed, 32-bit signed
        if sampwidth == 1:
            data = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
            data = (data - 128.0) / 128.0              # map to [-1,1]
        elif sampwidth == 2:
            data = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
            data = data / 32768.0
        elif sampwidth == 4:
            data = np.frombuffer(raw, dtype=np.int32).astype(np.float32)
            data = data / 2147483648.0
        else:
            print("Unsupported WAV sample width. Use 8-bit, 16-bit, or 32-bit PCM WAV.")
            return

        # If stereo, take left channel only (simple and common for homework)
        if n_channels > 1:
            data = data.reshape(-1, n_channels)
            data = data[:, 0]

        # This is our "analog" voice waveform (already sampled by the WAV fs)
        xs = data

        # Build time axis for plotting
        ts = np.arange(len(xs)) / float(fs)

        # Normalize once more (protect against clipping / weird files)
        peak = np.max(np.abs(xs))
        if peak > 1e-12:
            xs = xs / peak

        # Quantize -> encode -> decode
        xq, q_idx = quantize(xs, bits=q_bits)
        bitstream = encode_pcm(q_idx, bits=q_bits)
        q_rec = decode_pcm(bitstream, bits=q_bits)

        # Reconstruct using the same scaling (quantize used xmax=max(abs(xs)))
        xmax = np.max(np.abs(xs))
        levels = 2 ** q_bits
        delta = (2 * xmax) / levels
        x_rec = -xmax + q_rec * delta + (delta / 2)

        # Save reconstructed audio as WAV (16-bit PCM)
        out_fs = fs
        out_name = "recovered.wav"

        # Normalize to safe range before writing
        rec_peak = np.max(np.abs(x_rec))
        if rec_peak > 1e-12:
            x_rec_to_write = x_rec / rec_peak
        else:
            x_rec_to_write = x_rec

        x_int16 = np.int16(np.clip(x_rec_to_write, -1.0, 1.0) * 32767)

        try:
            with wave.open(out_name, "wb") as wf_out:
                wf_out.setnchannels(1)
                wf_out.setsampwidth(2)       # 16-bit
                wf_out.setframerate(out_fs)
                wf_out.writeframes(x_int16.tobytes())
            print(f"Saved reconstructed audio as: {out_name}")
        except Exception as e:
            print(f"Could not write recovered.wav: {e}")

    # ------------------- Common prints (both modes) -------------------
    print("\n===== RESULT (Section 3: Analog -> Digital / PCM) =====")
    print(f"Samples taken: {len(xs)}")
    print(f"Bits per sample: {q_bits}")
    print(f"Total bits sent: {len(bitstream)}")

    # Show first few samples as bit groups
    preview_samples = min(8, len(q_idx))
    groups = []
    for i in range(preview_samples):
        start = i * q_bits
        end = start + q_bits
        groups.append("".join(str(b) for b in bitstream[start:end]))
    print(f"First {preview_samples} samples as bits:", " | ".join(groups))

    # Optional: if WAV mode, show file sample rate used
    if out_fs is not None:
        print(f"WAV sample rate used: {out_fs} Hz")

    # ---- Benchmark (same idea as before) ----
    avg_quant = benchmark(lambda: quantize(xs, bits=q_bits), runs=20)
    avg_enc = benchmark(lambda: encode_pcm(q_idx, bits=q_bits), runs=20)
    avg_dec = benchmark(lambda: decode_pcm(bitstream, bits=q_bits), runs=20)
    print(f"[Benchmark S3] quant: {avg_quant:.6f}s | enc: {avg_enc:.6f}s | dec: {avg_dec:.6f}s")

    # ------------------- Plots -------------------
    # For WAV we don't have a separate "smooth analog" curve, so we just plot the waveform itself.

    # Plot original vs reconstructed (zoom to first 0.05s if WAV is long)
    plt.figure()
    plt.plot(ts, xs, label="Input (analog samples)")
    plt.plot(ts, x_rec, alpha=0.7, label="Reconstructed (from PCM)")
    plt.legend()
    plt.title("Input vs Reconstructed (Section 3)")
    plt.grid(True)

    # Plot quantized staircase (for WAV, this looks busy, but still valid)
    plt.figure()
    plt.plot(ts, xs, alpha=0.4, label="Input")
    plt.plot(ts, xq, label="Quantized")
    plt.legend()
    plt.title("Quantized Signal (Section 3)")
    plt.grid(True)

    plt.show()


# -------------------------
# Section 4: Analog -> Analog (AM / PM / FM)
# -------------------------
def run_section4():
    # Choose modulation type (only ONE choice)
    scheme = ask_choice(
        "Section 4: Choose analog modulation",
        [("1", "AM"), ("2", "PM"), ("3", "FM")]
    )
    scheme_map = {"1": "am", "2": "pm", "3": "fm"}
    scheme_name = scheme_map[scheme]

    # Ask shared parameters
    fm = ask_float("Message frequency fm (Hz): ")
    fc = ask_float("Carrier frequency fc (Hz): ")

    if fm <= 0:
        print("fm must be > 0.")
        return
    if fc <= 0:
        print("fc must be > 0.")
        return

    # For clean analog modulation, carrier should be much higher than message
    if fc < 10 * fm:
        print("Warning: for clean modulation, try fc >= 10*fm.")

    # Ask only the needed sensitivity/index
    if scheme_name == "am":
        ka = ask_float("AM modulation index ka (0..1): ")
        if not (0 <= ka <= 1):
            print("ka must be between 0 and 1.")
            return
    elif scheme_name == "pm":
        kp = ask_float("PM phase sensitivity kp (radians): ")
        if kp <= 0:
            print("kp must be > 0.")
            return
    else:  # fm
        kf = ask_float("FM frequency sensitivity kf (Hz): ")
        if kf <= 0:
            print("kf must be > 0.")
            return

    # Time axis (high enough sample rate to show carrier nicely)
    import numpy as np
    duration = 1.0
    samples_per_carrier_cycle = 100
    fs_plot = max(2000, int(samples_per_carrier_cycle * fc))
    t = np.linspace(0, duration, int(fs_plot * duration), endpoint=False)

    # Message signal
    m = np.sin(2 * np.pi * fm * t)

    # Modulate + Demodulate
    if scheme_name == "am":
        ka = ask_float("Modulation index ka (0..1): ")
        if not (0 <= ka <= 1):
            print("ka must be between 0 and 1.")
            return
        s = am_modulate(m, t, fc=fc, ka=ka)
        m_rec = am_demodulate(s, t, fc=fc)
        title_mod = "AM Modulated Signal"
        title_rec = "Recovered Message (AM)"
    elif scheme_name == "pm":
        kp = ask_float("PM phase sensitivity kp (rad): ")
        if kp <= 0:
            print("kp must be > 0.")
            return
        s = pm_modulate(m, t, fc=fc, kp=kp)
        m_rec = pm_demodulate(s, t, fc=fc, kp=kp)
        title_mod = "PM Modulated Signal"
        title_rec = "Recovered Message (PM)"
    else:
        kf = ask_float("FM frequency sensitivity kf (Hz): ")
        if kf <= 0:
            print("kf must be > 0.")
            return
        s = fm_modulate(m, t, fc=fc, kf=kf)
        m_rec = fm_demodulate(s, t, fc=fc, kf=kf)
        title_mod = "FM Modulated Signal"
        title_rec = "Recovered Message (FM)"

    print(f"\n===== RESULT (Section 4: Analog -> Analog / {scheme_name.upper()}) =====")
    print("Modulation/demodulation finished.")

    # Benchmark (same style as your other sections)
    if scheme_name == "am":
        avg_mod = benchmark(lambda: am_modulate(m, t, fc=fc, ka=ka), runs=30)
        avg_dem = benchmark(lambda: am_demodulate(s, t, fc=fc), runs=30)
    elif scheme_name == "pm":
        avg_mod = benchmark(lambda: pm_modulate(m, t, fc=fc, kp=kp), runs=30)
        avg_dem = benchmark(lambda: pm_demodulate(s, t, fc=fc, kp=kp), runs=30)
    else:
        avg_mod = benchmark(lambda: fm_modulate(m, t, fc=fc, kf=kf), runs=30)
        avg_dem = benchmark(lambda: fm_demodulate(s, t, fc=fc, kf=kf), runs=30)

    print(f"[Benchmark S4] mod: {avg_mod:.6f}s | demod: {avg_dem:.6f}s")

    # Plots (keep consistent and readable)
    plt.figure()
    plt.plot(t, m)
    plt.title("Original Message Signal (Section 4)")
    plt.xlabel("Time (s)")
    plt.grid(True)

    plt.figure()
    plt.plot(t, s)
    plt.title(f"{title_mod} (Section 4)")
    plt.xlabel("Time (s)")
    plt.grid(True)

    plt.figure()
    plt.plot(t, m_rec)
    plt.title(f"{title_rec} (Section 4)")
    plt.xlabel("Time (s)")
    plt.grid(True)

    plt.show()



# -------------------------
# Main menu
# -------------------------
def main():
    mode = ask_choice(
        "Choose conversion mode",
        [   ("1", "Digital -> Digital"),
            ("2", "Digital -> Analog"),
            ("3", "Analog -> Digital"),
            ("4", "Analog -> Analog")]
    )

    if mode == "1":
        run_section1()
    elif mode == "2":
        run_section2()
    elif mode == "3":
        run_section3()
    elif mode == "4":
        run_section4()


if __name__ == "__main__":
    main()
