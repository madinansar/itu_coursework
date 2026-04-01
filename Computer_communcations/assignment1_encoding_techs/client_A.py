import socket
import json
import numpy as np
import matplotlib.pyplot as plt
import wave

from ui import ask_choice, ask_bits, ask_int, ask_float
from d2d_claude import encode
from d2a_claude import modulate
from a2d_claude import analog_signal, sample_signal, quantize, encode_pcm
from a2a_claude import am_modulate

HOST = "127.0.0.1"
PORT = 50007


def send_request(req):
    msg = json.dumps(req).encode("utf-8")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(msg)
        s.shutdown(socket.SHUT_WR)
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
    return json.loads(data.decode("utf-8"))


def plot_wave(t, y, title, xlabel="Time", ylabel="Amplitude"):
    plt.figure()
    plt.plot(t, y)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.tight_layout()


def main():
    mode = ask_choice(
        "Choose conversion mode (Computer A -> Computer B)",
        [("1", "Digital -> Digital (send encoded waveform to B)"),
         ("2", "Digital -> Analog (send modulated signal to B)"),
         ("3", "Analog -> Digital (send PCM bitstream to B)"),
         ("4", "Analog -> Analog (send AM signal to B)")]
    )

    # ---------------- MODE 1 ----------------
    if mode == "1":
        bits_str = ask_bits("1011001")
        spb = ask_int("Samples per bit (Manchester needs even)", 100)

        scheme_key = ask_choice(
            "Mode 1: Choose line coding scheme",
            [("1", "NRZ-L"), ("2", "NRZ-I"), ("3", "Manchester"), ("4", "AMI")]
        )
        scheme_map = {"1": "nrz-l", "2": "nrz-i", "3": "manchester", "4": "ami"}
        scheme = scheme_map[scheme_key]

        t, x = encode(bits_str, scheme, samples_per_bit=spb)

        req = {
            "mode": 1,
            "scheme": scheme,
            "samples_per_bit": spb,
            "x": x.tolist(),
            "original_bits": [int(c) for c in bits_str]
        }

        resp = send_request(req)

        print("\n[A][Mode 1] Sent encoded waveform to B.")
        print("[A] Original bits:", [int(c) for c in bits_str])
        print("[B] Decoded  bits:", resp.get("decoded_bits"))
        print("[A] Match?", resp.get("decoded_bits") == [int(c) for c in bits_str])

        plot_wave(t, x, f"[Sender A] Encoded waveform ({scheme})", xlabel="Time (bit periods)")
        for k in range(len(bits_str) + 1):
            plt.axvline(k, linewidth=0.8)
        plt.show()
        return

    # ---------------- MODE 2 ----------------
    if mode == "2":
        bits_str = ask_bits("1011001")
        bit_rate = ask_float("Bit rate Rb (bits/s)", 1.0)
        fs = ask_float("Sampling frequency fs (Hz)", 200.0)
        fc = ask_float("Carrier frequency fc (Hz)", 10.0)

        scheme_key = ask_choice(
            "Mode 2: Choose modulation scheme",
            [("1", "ASK (OOK)"), ("2", "FSK"), ("3", "BPSK")]
        )
        scheme_map = {"1": "ask", "2": "fsk", "3": "bpsk"}
        scheme = scheme_map[scheme_key]

        t, s = modulate(bits_str, scheme, bit_rate=bit_rate, fs=fs, fc=fc)

        req = {
            "mode": 2,
            "scheme": scheme,
            "bit_rate": bit_rate,
            "fs": fs,
            "fc": fc,
            "t": t.tolist(),
            "s": s.tolist(),
            "original_bits": [int(c) for c in bits_str]
        }

        resp = send_request(req)

        print("\n[A][Mode 2] Sent modulated signal to B.")
        print("[A] Original bits:", [int(c) for c in bits_str])
        print("[B] Recovered bits:", resp.get("recovered_bits"))
        print("[A] Match?", resp.get("recovered_bits") == [int(c) for c in bits_str])

        plot_wave(t, s, f"[Sender A] {scheme.upper()} signal sent", xlabel="Time (s)")
        plt.show()
        return

        # ---------------- MODE 3 ----------------
    if mode == "3":
        src = ask_choice(
            "Mode 3 input source",
            [("1", "Synthetic sine wave"), ("2", "WAV audio file (.wav)")]
        )

        q_bits = ask_int("Quantization bits per sample", 8)

        if src == "1":
            fm = ask_float("Message frequency fm (Hz)", 2.0)

            # Dense "analog-like" time base for plotting only
            t_dense = np.linspace(0, 1, 5000)
            x_dense = analog_signal(t_dense, f=fm)

            # Choose sampling frequency for PCM
            fs = ask_float("Sampling frequency fs (Hz)", 50.0)

            ts, xs = sample_signal(x_dense, fs, t_dense)

        else:
            wav_name = input("Enter WAV filename (example: voice.wav): ").strip()
            if wav_name == "":
                wav_name = "voice.wav"

            max_sec = ask_float("Max seconds to transmit (keep small)", 3.0)

            fs, audio = read_wav_mono_float(wav_name, max_seconds=max_sec)

            # For PCM chain, we treat the wav samples as our sampled signal
            # So ts is optional; create a time axis for plotting
            ts = np.arange(len(audio)) / fs
            xs = audio

            print(f"[A] Loaded WAV: fs={fs} Hz, samples={len(xs)}")

        # Quantize and PCM encode
        xq, q_idx = quantize(xs, bits=q_bits)
        bitstream = encode_pcm(q_idx, bits=q_bits)

        levels = 2 ** q_bits
        xmax = float(np.max(np.abs(xs))) if len(xs) else 1.0
        delta = float((2 * xmax) / levels) if xmax != 0 else 1.0

        # Send to B
        req = {
            "mode": 3,
            "source_type": "sine" if src == "1" else "wav",
            "fs_audio": float(fs),
            "q_bits": int(q_bits),
            "bitstream": bitstream,
            "xmax": xmax,
            "delta": delta,

            # send a small preview (first N samples) for plotting at B
            "preview_ts": ts[:2000].tolist(),
            "preview_xs": xs[:2000].tolist(),
            "total_samples": int(len(xs))
        }

        resp = send_request(req)

        print("\n[A][Mode 3] Sent PCM bitstream to B.")
        print("[B] Meta:", resp.get("meta"))
        print("[B] Saved file:", resp.get("saved_wav", "N/A"))

        # Plot at A (preview)
        plt.figure()
        plt.plot(ts[:2000], xs[:2000])
        plt.title("[Sender A] Original signal preview (first part)")
        plt.grid(True)
        plt.tight_layout()

        plt.figure()
        plt.plot(ts[:2000], xq[:2000])
        plt.title("[Sender A] Quantized preview (first part)")
        plt.grid(True)
        plt.tight_layout()

        plt.show()
        return


    # ---------------- MODE 4 ----------------
    if mode == "4":
        fm = ask_float("Message frequency fm (Hz)", 2.0)
        fc = ask_float("Carrier frequency fc (Hz)", 20.0)
        ka = ask_float("Modulation index ka (0..1 recommended)", 0.8)

        t = np.linspace(0, 1, 5000)
        m = np.sin(2 * np.pi * fm * t)
        s = am_modulate(m, t, fc=fc, ka=ka)

        req = {
            "mode": 4,
            "fc": fc,
            "t": t.tolist(),
            "s": s.tolist(),
            "m_original": m.tolist()
        }

        resp = send_request(req)
        m_rec = np.array(resp.get("m_rec", []), dtype=float)

        print("\n[A][Mode 4] Sent AM signal to B.")
        print("[B] Returned recovered message length:", len(m_rec))

        plot_wave(t, m, "[Sender A] Original message m(t)", xlabel="Time (s)")
        plot_wave(t, s, "[Sender A] AM signal sent s(t)", xlabel="Time (s)")
        plt.show()
        return


def read_wav_mono_float(path, max_seconds=3.0):
    """
    Reads a PCM WAV file, returns (fs, audio_float32_mono).
    Limits to max_seconds to keep socket payload small.
    """
    with wave.open(path, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        fs = wf.getframerate()
        n_frames = wf.getnframes()

        # Limit duration
        max_frames = int(fs * max_seconds)
        frames_to_read = min(n_frames, max_frames)

        raw = wf.readframes(frames_to_read)

    if sampwidth == 2:
        data = np.frombuffer(raw, dtype=np.int16)
        scale = 32768.0
    elif sampwidth == 1:
        data = np.frombuffer(raw, dtype=np.uint8).astype(np.int16) - 128
        scale = 128.0
    else:
        raise ValueError("Only 8-bit or 16-bit PCM WAV supported.")

    # reshape to channels
    if n_channels > 1:
        data = data.reshape(-1, n_channels)
        data = data[:, 0]  # take left channel

    audio = data.astype(np.float32) / scale

    # normalize to [-1, 1]
    m = float(np.max(np.abs(audio))) if len(audio) else 1.0
    if m > 0:
        audio = audio / m

    return fs, audio


if __name__ == "__main__":
    main()
