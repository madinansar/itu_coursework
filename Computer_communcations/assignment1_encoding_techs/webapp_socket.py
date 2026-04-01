"""
Web-based Communication System with Real Socket Communication
This Flask app acts as a bridge between the web UI and the actual client_A/server_B socket communication.
"""

from flask import Flask, render_template, request, jsonify
import socket
import json
import threading
import time
import numpy as np

# Import encoding/decoding modules
from digital2digital import encode as d2d_encode
from digital2analog import modulate as d2a_modulate
from analog2digital import analog_signal, sample_signal, quantize, encode_pcm
from analog2analog import am_modulate, fm_modulate, pm_modulate

app = Flask(__name__)

# Configuration
HOST = "127.0.0.1"
PORT = 50007

# Storage for received data from server_B
received_data = {
    'has_data': False,
    'result': None,
    'timestamp': None
}

@app.route('/')
def index():
    return render_template('index_socket.html')

@app.route('/check_server', methods=['GET'])
def check_server():
    """Check if server_B is running and listening"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((HOST, PORT))
            if result == 0:
                return jsonify({'running': True, 'message': 'Server is running on port 50007'})
            else:
                return jsonify({'running': False, 'message': 'Server not responding on port 50007'})
    except Exception as e:
        return jsonify({'running': False, 'message': f'Error: {str(e)}'})

@app.route('/send_d2d', methods=['POST'])
def send_d2d():
    """Send Digital-to-Digital encoding request to server_B"""
    try:
        data = request.json
        bits = data['bits']
        scheme = data['scheme']
        samples_per_bit = data.get('samples_per_bit', 100)
        A = data.get('amplitude', 1.0)
        
        # Encode the signal using original code
        t, x = d2d_encode(bits, scheme, samples_per_bit, A)
        
        # Prepare request for server_B
        req = {
            'mode': 'd2d',
            'scheme': scheme,
            'signal': x.tolist(),
            'samples_per_bit': samples_per_bit,
            'amplitude': A,
            'original_bits': bits if isinstance(bits, str) else ''.join(map(str, bits))
        }
        
        # Send to server_B via socket
        response = send_to_server(req)
        
        return jsonify({
            'success': True,
            'sent_data': {
                'time': t.tolist(),
                'signal': x.tolist(),
                'original_bits': req['original_bits']
            },
            'server_response': response
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/send_d2a', methods=['POST'])
def send_d2a():
    """Send Digital-to-Analog modulation request to server_B"""
    try:
        data = request.json
        bits = data['bits']
        scheme = data['scheme']
        bit_rate = data.get('bit_rate', 1.0)  # Uses bit_rate, not samples_per_bit
        fs = data.get('sampling_rate', 200.0)  # sampling frequency
        fc = data.get('carrier_freq', 10.0)
        A = data.get('amplitude', 1.0)
        df = data.get('freq_dev', None)  # Frequency deviation for FSK

        # Modulate the signal using original code
        t, x = d2a_modulate(bits, scheme, bit_rate=bit_rate, fs=fs, fc=fc, df=df, A=A)
        
        # Prepare request for server_B
        req = {
            'mode': 'd2a',
            'scheme': scheme,
            'signal': x.tolist(),
            'bit_rate': bit_rate,
            'fs': fs,
            'carrier_freq': fc,
            'amplitude': A,
            'df': df,
            'original_bits': bits if isinstance(bits, str) else ''.join(map(str, bits))
        }
        
        # Send to server_B via socket
        response = send_to_server(req)
        
        return jsonify({
            'success': True,
            'sent_data': {
                'time': t.tolist(),
                'signal': x.tolist(),
                'original_bits': req['original_bits']
            },
            'server_response': response
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/send_a2d', methods=['POST'])
def send_a2d():
    """Send Analog-to-Digital encoding request to server_B"""
    try:
        data = request.json
        freq = data.get('signal_freq', 5.0)
        duration = data.get('duration', 1.0)
        fs = data.get('sampling_rate', 1000)
        bits = data.get('n_bits', 3)  # Uses 'bits' not 'n_bits'
        
        # Generate and encode analog signal using original code
        t = np.linspace(0, duration, int(fs * duration))
        analog_sig = analog_signal(t, f=freq)
        
        # Sample the signal
        t_samples, x_samples = sample_signal(analog_sig, fs, t)
        
        # Quantize
        xq, q_indices = quantize(x_samples, bits=bits)
        
        # Encode to PCM
        pcm_bits = encode_pcm(q_indices, bits=bits)
        pcm_bitstream = ''.join(map(str, pcm_bits))
        
        # Prepare request for server_B
        req = {
            'mode': 'a2d',
            'pcm_bits': pcm_bitstream,
            'bits': bits,
            'original_signal': analog_sig.tolist()
        }
        
        # Send to server_B via socket
        response = send_to_server(req)
        
        return jsonify({
            'success': True,
            'sent_data': {
                'time': t.tolist(),
                'analog_signal': analog_sig.tolist(),
                'quantized_signal': xq.tolist(),
                'pcm_bits': pcm_bitstream,
                'n_bits': bits
            },
            'server_response': response
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/send_a2a', methods=['POST'])
def send_a2a():
    """Send Analog-to-Analog modulation request to server_B"""
    try:
        data = request.json
        scheme = data['scheme']  # am, fm, or pm
        fm = data.get('message_freq', 5.0)
        fc = data.get('carrier_freq', 50.0)
        ka = data.get('modulation_index', 0.5)
        kf = data.get('freq_sensitivity', 5.0)  # for FM
        kp = data.get('phase_sensitivity', 2.0)  # for PM
        duration = data.get('duration', 1.0)
        fs = data.get('sampling_rate', 1000)
        
        # Generate message signal
        t = np.linspace(0, duration, int(fs * duration))
        message = np.sin(2 * np.pi * fm * t)
        
        # Modulate based on scheme
        if scheme == 'am':
            modulated = am_modulate(message, t, fc=fc, ka=ka)
        elif scheme == 'fm':
            modulated = fm_modulate(message, t, fc=fc, kf=kf)
        elif scheme == 'pm':
            modulated = pm_modulate(message, t, fc=fc, kp=kp)
        else:
            return jsonify({'success': False, 'error': f'Unknown scheme: {scheme}'})
        
        # Prepare request for server_B
        req = {
            'mode': 'a2a',
            'scheme': scheme,
            'signal': modulated.tolist(),
            'carrier_freq': fc,
            'time': t.tolist(),
            'ka': ka,
            'kf': kf,
            'kp': kp,
            'original_message': message.tolist()
        }
        
        # Send to server_B via socket
        response = send_to_server(req)
        
        return jsonify({
            'success': True,
            'sent_data': {
                'time': t.tolist(),
                'message_signal': message.tolist(),
                'modulated_signal': modulated.tolist()
            },
            'server_response': response
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def send_to_server(req):
    """
    Send request to server_B via TCP socket (mimics client_A behavior)
    """
    try:
        msg = json.dumps(req).encode("utf-8")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((HOST, PORT))
            s.sendall(msg)
            s.shutdown(socket.SHUT_WR)
            
            # Receive response
            data = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
            
            response = json.loads(data.decode("utf-8"))
            return response
            
    except socket.timeout:
        return {'error': 'Server timeout - no response received'}
    except ConnectionRefusedError:
        return {'error': 'Connection refused - is server_B running?'}
    except Exception as e:
        return {'error': f'Socket error: {str(e)}'}

if __name__ == '__main__':
    print("=" * 60)
    print("Web-based Communication System with Real Socket Communication")
    print("=" * 60)
    print("\nIMPORTANT: You must start server_B.py FIRST in a separate terminal!")
    print(f"Server should be listening on {HOST}:{PORT}")
    print("\nSteps:")
    print("1. Open a new terminal")
    print("2. Run: cd blg337 && python server_B.py")
    print("3. Then access this web interface at: http://127.0.0.1:5001")
    print("=" * 60)
    print("\nStarting Flask web server...")
    app.run(debug=True, host='0.0.0.0', port=5001)
