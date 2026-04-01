"""
Modified server_B.py to work with web interface
This version handles JSON requests in the format sent by webapp_socket.py
while maintaining compatibility with the original client_A.py
"""

import socket
import json
import numpy as np

# Import decoding modules
from digital2digital import decode as d2d_decode
from digital2analog import demodulate as d2a_demodulate
from analog2digital import decode_pcm
from analog2analog import am_demodulate, fm_demodulate, pm_demodulate

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


def handle_request(req):
    """
    Handle requests from both web interface and original client_A
    Web interface sends: {'mode': 'd2d', 'scheme': 'nrz-l', ...}
    Original client_A sends: {'mode': 1, 'scheme': 'nrz-l', ...}
    """
    mode = req.get("mode")
    
    # Mode conversion
    if isinstance(mode, str):
        mode_map = {'d2d': 1, 'd2a': 2, 'a2d': 3, 'a2a': 4}
        mode_num = mode_map.get(mode, 0)
        mode_str = mode
    else:
        mode_num = mode
        mode_map_reverse = {1: 'd2d', 2: 'd2a', 3: 'a2d', 4: 'a2a'}
        mode_str = mode_map_reverse.get(mode, 'unknown')

    # =========================
    # MODE 1 / D2D: Digital -> Digital
    # =========================
    if mode_num == 1:
        scheme = req["scheme"]
        spb = int(req.get("samples_per_bit", 100))
        
        # Handle both 'x' (old format) and 'signal' (new format)
        if 'signal' in req:
            x = np.array(req["signal"], dtype=float)
        else:
            x = np.array(req["x"], dtype=float)
            
        amplitude = float(req.get("amplitude", 1.0))
        original_bits = req.get("original_bits", None)

        # Original implementation: decode(x, scheme, samples_per_bit, A, initial_level)
        decoded_bits = d2d_decode(x, scheme, samples_per_bit=spb, A=amplitude)
        decoded_str = ''.join(map(str, decoded_bits))

        print("\n[Server B] Digital -> Digital")
        print(f"[Server B] Scheme: {scheme}")
        print(f"[Server B] Samples per bit: {spb}")
        print(f"[Server B] Amplitude: {amplitude}")
        if original_bits is not None:
            print(f"[Server B] Original bits: {original_bits}")
        print(f"[Server B] Decoded  bits: {decoded_str}")
        if original_bits is not None:
            match = (decoded_str == original_bits)
            print(f"[Server B] Match? {match} {'✓' if match else '✗'}")

        return {
            "ok": True, 
            "mode": mode_str,
            "decoded_bits": decoded_str,
            "original_bits": original_bits,
            "match": decoded_str == original_bits if original_bits else None
        }

    # =========================
    # MODE 2 / D2A: Digital -> Analog
    # =========================
    elif mode_num == 2:
        scheme = req["scheme"]
        bit_rate = float(req.get("bit_rate", 1.0))
        fs = float(req.get("fs", 200.0))
        fc = float(req.get("carrier_freq", 10.0))
        A = float(req.get("amplitude", 1.0))
        df = req.get("df") # Frequency deviation for FSK
        
        # Handle both formats
        if 'signal' in req:
            t = np.array(req.get("time", []), dtype=float) if 'time' in req else None
            signal = req["signal"]
        else:
            t = np.array(req.get("t", []), dtype=float) if 't' in req else None
            signal = req["s"]
            
        original_bits = req.get("original_bits", None)

        # Original implementation: demodulate(t, s, scheme, bit_rate, fs, fc, A)
        # Convert to numpy arrays because digital2analog.py expects them for math operations
        s_arr = np.array(signal, dtype=float)
        
        if t is not None and len(t) > 0:
            t_arr = t # already np.array from above parsing
        else:
            t_arr = np.arange(len(s_arr)) / fs
        
        recovered_bits = d2a_demodulate(t_arr, s_arr, scheme, 
                                        bit_rate=bit_rate, fs=fs, fc=fc, df=df, A=A)
        recovered_str = ''.join(map(str, recovered_bits))

        print("\n[Server B] Digital -> Analog")
        print(f"[Server B] Scheme: {scheme}")
        print(f"[Server B] Carrier frequency: {fc} Hz")
        print(f"[Server B] Bit rate: {bit_rate} bps")
        if original_bits is not None:
            print(f"[Server B] Original bits: {original_bits}")
        print(f"[Server B] Recovered bits: {recovered_str}")
        if original_bits is not None:
            match = (recovered_str == original_bits)
            print(f"[Server B] Match? {match}")

        return {
            "ok": True,
            "mode": mode_str,
            "recovered_bits": recovered_str,
            "original_bits": original_bits,
            "match": recovered_str == original_bits if original_bits else None
        }

    # =========================
    # MODE 3 / A2D: Analog -> Digital (PCM)
    # =========================
    elif mode_num == 3:
        bits = int(req.get("bits", req.get("n_bits", 3)))
        pcm_bits = req["pcm_bits"]
        
        # Convert string to list if needed
        if isinstance(pcm_bits, str):
            pcm_bits = [int(b) for b in pcm_bits]
        
        # Original implementation: decode_pcm(bitstream, bits)
        q_indices = decode_pcm(pcm_bits, bits=bits)
        
        # Reconstruct signal from indices
        levels = 2 ** bits
        xmax = 1.0  # Assume normalized
        delta = (2 * xmax) / levels
        reconstructed = -xmax + q_indices * delta + delta / 2

        print("\n[Server B] Analog -> Digital (PCM)")
        print(f"[Server B] Quantization bits: {bits}")
        print(f"[Server B] PCM bitstream length: {len(pcm_bits)} bits")
        print(f"[Server B] Reconstructed samples: {len(reconstructed)}")

        return {
            "ok": True,
            "mode": mode_str,
            "reconstructed_signal": reconstructed.tolist(),
            "samples": len(reconstructed)
        }

    # =========================
    # MODE 4 / A2A: Analog -> Analog (AM/FM/PM)
    # =========================
    elif mode_num == 4:
        fc = float(req["carrier_freq"])
        scheme = req.get("scheme", "am").lower()
        
        # Handle both formats
        if 'signal' in req:
            signal = np.array(req["signal"], dtype=float)
            t = np.array(req.get("time", []), dtype=float) if 'time' in req else None
        else:
            signal = np.array(req["s"], dtype=float)
            t = np.array(req.get("t", []), dtype=float) if 't' in req else None

        # Demodulate based on scheme
        if scheme == "am":
            ka = float(req.get("ka", 0.5))
            demodulated = am_demodulate(signal, t, fc=fc)
            print(f"\n[Server B] Analog -> Analog (AM)")
            print(f"[Server B] Modulation index (ka): {ka}")
        elif scheme == "fm":
            kf = float(req.get("kf", 5.0))
            demodulated = fm_demodulate(signal, t, fc=fc, kf=kf)
            print(f"\n[Server B] Analog -> Analog (FM)")
            print(f"[Server B] Frequency sensitivity (kf): {kf}")
        elif scheme == "pm":
            kp = float(req.get("kp", 2.0))
            demodulated = pm_demodulate(signal, t, fc=fc, kp=kp)
            print(f"\n[Server B] Analog -> Analog (PM)")
            print(f"[Server B] Phase sensitivity (kp): {kp}")
        else:
            return {"ok": False, "error": f"Unknown A2A scheme: {scheme}"}

        print(f"[Server B] Carrier frequency: {fc} Hz")
        print(f"[Server B] Demodulated samples: {len(demodulated)}")

        return {
            "ok": True,
            "mode": mode_str,
            "scheme": scheme.upper(),
            "demodulated_signal": demodulated.tolist()
        }

    return {"ok": False, "error": f"Unknown mode: {mode}"}


def main():
    print("=" * 70)
    print(f"[Server B] Starting on {HOST}:{PORT}")
    print("=" * 70)
    print("Listening for connections from:")
    print("  - Web interface (webapp_socket.py)")
    print("  - Original client_A.py")
    print("\nWaiting for connections...")
    print("=" * 70)
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(5)

        connection_count = 0
        while True:
            conn, addr = srv.accept()
            connection_count += 1
            with conn:
                print(f"\n[Connection #{connection_count}] Connected by {addr}")
                raw = recv_all(conn)
                if not raw:
                    print("[Server B] Empty request")
                    continue

                try:
                    req = json.loads(raw.decode("utf-8"))
                except Exception as e:
                    print(f"[Server B] JSON parse error: {e}")
                    send_json(conn, {"ok": False, "error": "Invalid JSON"})
                    continue

                resp = handle_request(req)
                send_json(conn, resp)
                print(f"[Server B] Response sent: {resp.get('mode', 'unknown')} - OK={resp.get('ok', False)}")
                print("-" * 70)


if __name__ == "__main__":
    main()
