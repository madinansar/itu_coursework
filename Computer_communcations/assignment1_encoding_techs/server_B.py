import socket
import json
import numpy as np
import matplotlib.pyplot as plt
import wave

from d2d_claude import decode
from d2a_claude import demodulate
from a2d_claude import decode_pcm
from a2a_claude import am_demodulate

HOST = "127.0.0.1"
PORT = 50007


def recv_all(conn):
    data = b""
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            break
        data += chunk
    return data


def send_json(conn, obj):
    msg = json.dumps(obj).encode("utf-8")
    conn.sendall(msg)


def plot_wave(t, y, title, xlabel="Time", ylabel="Amplitude"):
    plt.figure()
    plt.plot(t, y)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.tight_layout()

def write_wav_int16(path, fs, x_float):
    """
    Writes mono 16-bit PCM WAV from float array in [-1, 1].
    """
    x = np.clip(x_float, -1.0, 1.0)
    data = (x * 32767.0).astype(np.int16)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(int(fs))
        wf.writeframes(data.tobytes())


def handle_request(req):
    mode = req.get("mode")

    # =========================
    # MODE 1: Digital -> Digital
    # =========================
    if mode == 1:
        scheme = req["scheme"]
        spb = int(req["samples_per_bit"])
        x = np.array(req["x"], dtype=float)

        original_bits = req.get("original_bits", None)

        decoded_bits = decode(x.tolist(), scheme, samples_per_bit=spb)

        print("\n[B][Mode 1] Digital -> Digital")
        print("[B] Scheme:", scheme)
        if original_bits is not None:
            print("[B] Original bits (from A):", original_bits)
        print("[B] Decoded  bits:", decoded_bits)
        if original_bits is not None:
            print("[B] Match?", decoded_bits == original_bits)

        # Plot received waveform at B
        t = np.arange(len(x)) / spb
        plot_wave(t, x, f"[Receiver B] Received encoded waveform ({scheme})",
                  xlabel="Time (bit periods)")
        # bit boundary lines
        for k in range(len(decoded_bits) + 1):
            plt.axvline(k, linewidth=0.8)

        plt.show()

        return {"ok": True, "mode": 1, "decoded_bits": decoded_bits}

    # =========================
    # MODE 2: Digital -> Analog
    # =========================
    if mode == 2:
        scheme = req["scheme"]
        bit_rate = float(req["bit_rate"])
        fs = float(req["fs"])
        fc = float(req["fc"])

        t = np.array(req["t"], dtype=float)
        s = np.array(req["s"], dtype=float)

        original_bits = req.get("original_bits", None)

        recovered_bits = demodulate(t.tolist(), s.tolist(), scheme,
                                    bit_rate=bit_rate, fs=fs, fc=fc)

        print("\n[B][Mode 2] Digital -> Analog")
        print("[B] Scheme:", scheme)
        if original_bits is not None:
            print("[B] Original bits (from A):", original_bits)
        print("[B] Recovered bits:", recovered_bits)
        if original_bits is not None:
            print("[B] Match?", recovered_bits == original_bits)

        # Plot received modulated signal at B
        plot_wave(t, s, f"[Receiver B] Received {scheme.upper()} signal",
                  xlabel="Time (s)")
        plt.show()

        return {"ok": True, "mode": 2, "recovered_bits": recovered_bits}

    # =========================
    # MODE 3: Analog -> Digital (PCM)
    # =========================
    if mode == 3:
        q_bits = int(req["q_bits"])
        fs_audio = float(req.get("fs_audio", 8000))
        bitstream = req["bitstream"]

        xmax = float(req.get("xmax", 1.0))
        delta = float(req.get("delta", 1.0))

        preview_ts = np.array(req.get("preview_ts", []), dtype=float)
        preview_xs = np.array(req.get("preview_xs", []), dtype=float)

        # Decode indices
        q_indices = np.array(decode_pcm(bitstream, bits=q_bits), dtype=int)

        # Reconstruct from indices
        x_rec = -xmax + q_indices * delta + delta / 2

        # Normalize safely for WAV output
        m = float(np.max(np.abs(x_rec))) if len(x_rec) else 1.0
        if m > 0:
            x_out = (x_rec / m).astype(np.float32)
        else:
            x_out = x_rec.astype(np.float32)

        out_name = "recovered.wav"
        write_wav_int16(out_name, fs_audio, x_out)

        print("\n[B][Mode 3] Analog -> Digital (PCM)")
        print("[B] fs_audio:", fs_audio, "Hz")
        print("[B] Bits/sample:", q_bits)
        print("[B] Total samples reconstructed:", len(x_out))
        print("[B] Saved:", out_name)

        # Plot preview: original vs reconstructed (first part)
        if len(preview_ts) > 0 and len(preview_xs) > 0:
            n = min(len(preview_xs), len(x_out), len(preview_ts))
            plt.figure()
            plt.plot(preview_ts[:n], preview_xs[:n], label="Original preview (from A)")
            plt.plot(preview_ts[:n], x_out[:n], label="Recovered preview (at B)", alpha=0.8)
            plt.title("[Receiver B] Mode 3: Original vs Recovered (preview)")
            plt.xlabel("Time (s)")
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.show()

        meta = {
            "source_type": req.get("source_type", "unknown"),
            "fs_audio": fs_audio,
            "q_bits": q_bits,
            "samples": int(len(x_out)),
            "total_bits": int(len(bitstream))
        }

        return {"ok": True, "mode": 3, "meta": meta, "saved_wav": out_name}


    # =========================
    # MODE 4: Analog -> Analog (AM)
    # =========================
    if mode == 4:
        fc = float(req["fc"])
        t = np.array(req["t"], dtype=float)
        s = np.array(req["s"], dtype=float)

        # optional original message from A
        m_original = req.get("m_original", None)

        m_rec = am_demodulate(s.tolist(), t.tolist(), fc=fc)
        m_rec = np.array(m_rec, dtype=float)

        print("\n[B][Mode 4] Analog -> Analog (AM)")
        print("[B] Carrier fc:", fc)
        print("[B] Received samples:", len(s))

        # Plot received AM signal and recovered message at B
        plot_wave(t, s, "[Receiver B] Received AM signal", xlabel="Time (s)")
        plot_wave(t, m_rec, "[Receiver B] Recovered message (envelope)", xlabel="Time (s)")

        # If A sent original message, plot overlay
        if m_original is not None:
            m_original = np.array(m_original, dtype=float)
            plt.figure()
            plt.plot(t, m_original, label="Original message (from A)")
            plt.plot(t, m_rec, label="Recovered message (at B)", alpha=0.8)
            plt.title("[Receiver B] Original vs Recovered (AM)")
            plt.xlabel("Time (s)")
            plt.grid(True)
            plt.legend()
            plt.tight_layout()

        plt.show()

        return {"ok": True, "mode": 4, "m_rec": m_rec.tolist()}

    return {"ok": False, "error": f"Unknown mode: {mode}"}


def main():
    print(f"[B] Server starting on {HOST}:{PORT} ...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(1)
        print("[B] Waiting for Computer A (client) connection...")

        while True:
            conn, addr = srv.accept()
            with conn:
                print(f"[B] Connected by {addr}")
                raw = recv_all(conn)
                if not raw:
                    print("[B] Empty request")
                    continue

                try:
                    req = json.loads(raw.decode("utf-8"))
                except Exception as e:
                    print("[B] JSON parse error:", e)
                    continue

                resp = handle_request(req)
                send_json(conn, resp)
                print("[B] Response sent.\n")


if __name__ == "__main__":
    main()
