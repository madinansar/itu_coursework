"""
COMPREHENSIVE BENCHMARK: All 4 Communication Modes
Compares: Original implementation vs Claude's vs Gemini's optimizations

Modes tested:
1. Digital-to-Digital (D2D): NRZ-L, NRZ-I, Manchester, AMI
2. Digital-to-Analog (D2A): ASK, FSK, BPSK
3. Analog-to-Digital (A2D): PCM encoding/decoding
4. Analog-to-Analog (A2A): AM modulation/demodulation
"""

import time
import tracemalloc
import sys
import numpy as np
import csv
import datetime
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

# Import Original implementations from blg337 folder
import digital2digital as d2d_user
import digital2analog as d2a_user
import analog2digital as a2d_user
import analog2analog as a2a_user

# Import Claude's implementations
from ai_optimizations.d2d_claude import encode as d2d_encode_claude, decode as d2d_decode_claude
from ai_optimizations.d2d_gemini import encode as d2d_encode_gemini, decode as d2d_decode_gemini

# Import D2A implementations
from ai_optimizations.d2a_claude import modulate as d2a_mod_claude, demodulate as d2a_demod_claude
from ai_optimizations.d2a_gemini import modulate as d2a_mod_gemini, demodulate as d2a_demod_gemini

# Import A2D implementations
from ai_optimizations.a2d_claude import (analog_signal as a2d_sig_claude, 
                                         quantize as a2d_quant_claude,
                                         encode_pcm as a2d_enc_claude,
                                         decode_pcm as a2d_dec_claude)
from ai_optimizations.a2d_gemini import (analog_signal as a2d_sig_gemini,
                                         quantize as a2d_quant_gemini, 
                                         encode_pcm as a2d_enc_gemini,
                                         decode_pcm as a2d_dec_gemini)

# Import A2A implementations
from ai_optimizations.a2a_claude import am_modulate as a2a_mod_claude, am_demodulate as a2a_demod_claude
from ai_optimizations.a2a_gemini import am_modulate as a2a_mod_gemini, am_demodulate as a2a_demod_gemini


class BenchmarkResult:
    def __init__(self, name: str):
        self.name = name
        self.encode_time = 0.0
        self.decode_time = 0.0
        self.encode_memory = 0
        self.decode_memory = 0
        self.total_time = 0.0
        self.total_memory = 0
        self.error = None


def generate_test_bits(bit_length: int = 256) -> Dict[str, str]:
    """Generate test bit patterns"""
    return {
        "all_zeros": "0" * bit_length,
        "all_ones": "1" * bit_length,
        "alternating": "01" * (bit_length // 2),
        "random": ''.join(np.random.choice(['0', '1'], bit_length)),
    }


# ==================== DIGITAL-TO-DIGITAL BENCHMARKS ====================

def benchmark_d2d_user(bits: str, scheme: str, spb: int = 100) -> BenchmarkResult:
    """Benchmark original D2D implementation"""
    result = BenchmarkResult("Original")
    
    try:
        # Use digital2digital.py
        # Encode
        tracemalloc.start()
        start = time.perf_counter()
        t, x = d2d_user.encode(bits, scheme, samples_per_bit=spb)
        result.encode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.encode_memory = peak
        
        # Decode
        tracemalloc.start()
        start = time.perf_counter()
        decoded_bits = d2d_user.decode(x, scheme, samples_per_bit=spb)
        result.decode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.decode_memory = peak
        
        result.total_time = result.encode_time + result.decode_time
        result.total_memory = result.encode_memory + result.decode_memory
        
        # Verify correctness
        decoded_str = ''.join(map(str, decoded_bits))
        if decoded_str != bits:
            result.error = "Decode mismatch"
    except Exception as e:
        result.error = str(e)
    
    return result


def benchmark_d2d_claude(bits: str, scheme: str, spb: int = 100) -> BenchmarkResult:
    result = BenchmarkResult("Claude")
    
    try:
        tracemalloc.start()
        start = time.perf_counter()
        t, x = d2d_encode_claude(bits, scheme, samples_per_bit=spb)
        result.encode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.encode_memory = peak
        
        tracemalloc.start()
        start = time.perf_counter()
        decoded_bits = d2d_decode_claude(x, scheme, samples_per_bit=spb)
        result.decode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.decode_memory = peak
        
        result.total_time = result.encode_time + result.decode_time
        result.total_memory = result.encode_memory + result.decode_memory
    except Exception as e:
        result.error = str(e)
    
    return result


def benchmark_d2d_gemini(bits: str, scheme: str, spb: int = 100) -> BenchmarkResult:
    result = BenchmarkResult("Gemini")
    
    try:
        tracemalloc.start()
        start = time.perf_counter()
        t, x = d2d_encode_gemini(bits, scheme, samples_per_bit=spb)
        result.encode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.encode_memory = peak
        
        tracemalloc.start()
        start = time.perf_counter()
        decoded_bits = d2d_decode_gemini(x, scheme, samples_per_bit=spb)
        result.decode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.decode_memory = peak
        
        result.total_time = result.encode_time + result.decode_time
        result.total_memory = result.encode_memory + result.decode_memory
    except Exception as e:
        result.error = str(e)
    
    return result


# ==================== DIGITAL-TO-ANALOG BENCHMARKS ====================

def benchmark_d2a_user(bits: str, scheme: str) -> BenchmarkResult:
    result = BenchmarkResult("Original")
    
    try:
        tracemalloc.start()
        start = time.perf_counter()
        # Pass df=3.0 so FSK works (fc=10 -> f0=7, f1=13)
        t, s = d2a_user.modulate(bits, scheme, bit_rate=1.0, fs=200.0, fc=10.0, df=3.0)
        result.encode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.encode_memory = peak
        
        tracemalloc.start()
        start = time.perf_counter()
        # Pass df=3.0 so FSK works
        decoded_bits = d2a_user.demodulate(t, s, scheme, bit_rate=1.0, fc=10.0, df=3.0)
        result.decode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.decode_memory = peak
        
        result.total_time = result.encode_time + result.decode_time
        result.total_memory = result.encode_memory + result.decode_memory
    except Exception as e:
        result.error = str(e)
    
    return result


def benchmark_d2a_claude(bits: str, scheme: str) -> BenchmarkResult:
    result = BenchmarkResult("Claude")
    
    try:
        tracemalloc.start()
        start = time.perf_counter()
        t, s = d2a_mod_claude(bits, scheme, bit_rate=1.0, fs=200.0, fc=10.0)
        result.encode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.encode_memory = peak
        
        tracemalloc.start()
        start = time.perf_counter()
        decoded_bits = d2a_demod_claude(s, t, scheme, bit_rate=1.0, fc=10.0)
        result.decode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.decode_memory = peak
        
        result.total_time = result.encode_time + result.decode_time
        result.total_memory = result.encode_memory + result.decode_memory
    except Exception as e:
        result.error = str(e)
    
    return result


def benchmark_d2a_gemini(bits: str, scheme: str) -> BenchmarkResult:
    result = BenchmarkResult("Gemini")
    
    try:
        tracemalloc.start()
        start = time.perf_counter()
        t, s = d2a_mod_gemini(bits, scheme, bit_rate=1.0, fs=200.0, fc=10.0)
        result.encode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.encode_memory = peak
        
        tracemalloc.start()
        start = time.perf_counter()
        decoded_bits = d2a_demod_gemini(s, t, scheme, bit_rate=1.0, fc=10.0)
        result.decode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.decode_memory = peak
        
        result.total_time = result.encode_time + result.decode_time
        result.total_memory = result.encode_memory + result.decode_memory
    except Exception as e:
        result.error = str(e)
    
    return result


# ==================== ANALOG-TO-DIGITAL BENCHMARKS ====================

def benchmark_a2d_user(signal_length: int = 1000) -> BenchmarkResult:
    result = BenchmarkResult("Original")
    
    try:
        # Generate analog signal
        t = np.linspace(0, 1, signal_length)
        x = a2d_user.analog_signal(t, f=2.0)
        
        # Encode (quantize + PCM)
        tracemalloc.start()
        start = time.perf_counter()
        xq, q_idx = a2d_user.quantize(x, bits=8)
        bitstream = a2d_user.encode_pcm(q_idx, bits=8)
        result.encode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.encode_memory = peak
        
        # Decode
        tracemalloc.start()
        start = time.perf_counter()
        q_idx_rec = a2d_user.decode_pcm(bitstream, bits=8)
        result.decode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.decode_memory = peak
        
        result.total_time = result.encode_time + result.decode_time
        result.total_memory = result.encode_memory + result.decode_memory
    except Exception as e:
        result.error = str(e)
    
    return result


def benchmark_a2d_claude(signal_length: int = 1000) -> BenchmarkResult:
    result = BenchmarkResult("Claude")
    
    try:
        # Generate analog signal
        t = np.linspace(0, 1, signal_length)
        x = a2d_sig_claude(t, f=2.0)
        
        # Encode (sample + quantize + PCM)
        tracemalloc.start()
        start = time.perf_counter()
        xq, q_idx = a2d_quant_claude(x, bits=8)
        bitstream = a2d_enc_claude(q_idx, bits=8)
        result.encode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.encode_memory = peak
        
        # Decode
        tracemalloc.start()
        start = time.perf_counter()
        q_idx_rec = a2d_dec_claude(bitstream, bits=8)
        result.decode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.decode_memory = peak
        
        result.total_time = result.encode_time + result.decode_time
        result.total_memory = result.encode_memory + result.decode_memory
    except Exception as e:
        result.error = str(e)
    
    return result


def benchmark_a2d_gemini(signal_length: int = 1000) -> BenchmarkResult:
    result = BenchmarkResult("Gemini")
    
    try:
        # Generate analog signal
        t = np.linspace(0, 1, signal_length)
        x = a2d_sig_gemini(t, f=2.0)
        
        # Encode
        tracemalloc.start()
        start = time.perf_counter()
        xq, q_idx = a2d_quant_gemini(x, bits=8)
        bitstream = a2d_enc_gemini(q_idx, bits=8)
        result.encode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.encode_memory = peak
        
        # Decode
        tracemalloc.start()
        start = time.perf_counter()
        q_idx_rec = a2d_dec_gemini(bitstream, bits=8)
        result.decode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.decode_memory = peak
        
        result.total_time = result.encode_time + result.decode_time
        result.total_memory = result.encode_memory + result.decode_memory
    except Exception as e:
        result.error = str(e)
    
    return result


# ==================== ANALOG-TO-ANALOG BENCHMARKS ====================
def benchmark_a2a_user(signal_length: int = 5000) -> BenchmarkResult:
    result = BenchmarkResult("Original")
    
    try:
        # Generate message signal
        t = np.linspace(0, 1, signal_length)
        m = np.sin(2 * np.pi * 2.0 * t)
        
        # Modulate
        tracemalloc.start()
        start = time.perf_counter()
        s = a2a_user.am_modulate(m, t, fc=20.0, ka=0.8)
        result.encode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.encode_memory = peak
        
        # Demodulate
        tracemalloc.start()
        start = time.perf_counter()
        m_rec = a2a_user.am_demodulate(s, t, fc=20.0)
        result.decode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.decode_memory = peak
        
        result.total_time = result.encode_time + result.decode_time
        result.total_memory = result.encode_memory + result.decode_memory
    except Exception as e:
        result.error = str(e)
    
    return result


def benchmark_a2a_claude(signal_length: int = 5000) -> BenchmarkResult:
    result = BenchmarkResult("Claude")
    
    try:
        # Generate message signal
        t = np.linspace(0, 1, signal_length)
        m = np.sin(2 * np.pi * 2.0 * t)
        
        # Modulate
        tracemalloc.start()
        start = time.perf_counter()
        s = a2a_mod_claude(m, t, fc=20.0, ka=0.8)
        result.encode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.encode_memory = peak
        
        # Demodulate
        tracemalloc.start()
        start = time.perf_counter()
        m_rec = a2a_demod_claude(s, t, fc=20.0)
        result.decode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.decode_memory = peak
        
        result.total_time = result.encode_time + result.decode_time
        result.total_memory = result.encode_memory + result.decode_memory
    except Exception as e:
        result.error = str(e)
    
    return result


def benchmark_a2a_gemini(signal_length: int = 5000) -> BenchmarkResult:
    result = BenchmarkResult("Gemini")
    
    try:
        # Generate message signal
        t = np.linspace(0, 1, signal_length)
        m = np.sin(2 * np.pi * 2.0 * t)
        
        # Modulate
        tracemalloc.start()
        start = time.perf_counter()
        s = a2a_mod_gemini(m, t, fc=20.0, ka=0.8)
        result.encode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.encode_memory = peak
        
        # Demodulate
        tracemalloc.start()
        start = time.perf_counter()
        m_rec = a2a_demod_gemini(s, t, fc=20.0)
        result.decode_time = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result.decode_memory = peak
        
        result.total_time = result.encode_time + result.decode_time
        result.total_memory = result.encode_memory + result.decode_memory
    except Exception as e:
        result.error = str(e)
    
    return result


# ==================== MAIN BENCHMARK RUNNER ====================

def format_result(r: BenchmarkResult) -> str:
    if r.error:
        return f"{r.name:8} | ERROR: {r.error}"
    return (f"{r.name:8} | Encode: {r.encode_time*1000:8.4f}ms {r.encode_memory/1024:8.2f}KB | "
            f"Decode: {r.decode_time*1000:8.4f}ms {r.decode_memory/1024:8.2f}KB | "
            f"Total: {r.total_time*1000:8.4f}ms {r.total_memory/1024:8.2f}KB")


def run_comprehensive_benchmark(bit_length: int = 256, iterations: int = 50):
    print("=" * 100)
    print("COMPREHENSIVE BENCHMARK: All 4 Communication Modes")
    print(f"Bit Length: {bit_length} | Iterations: {iterations}")
    print("=" * 100)
    
    test_cases = generate_test_bits(bit_length)
    csv_data = []
    
    # ========== MODE 1: DIGITAL-TO-DIGITAL ==========
    print("\n" + "=" * 100)
    print("MODE 1: DIGITAL-TO-DIGITAL (D2D)")
    print("=" * 100)
    
    d2d_schemes = ["nrz-l", "nrz-i", "manchester", "ami"]
    
    for scheme in d2d_schemes:
        print(f"\n--- Scheme: {scheme.upper()} ---")
        
        for test_name, bits in test_cases.items():
            print(f"\n  Test: {test_name}")
            
            # Run iterations
            user_results = [benchmark_d2d_user(bits, scheme) for _ in range(iterations)]
            claude_results = [benchmark_d2d_claude(bits, scheme) for _ in range(iterations)]
            gemini_results = [benchmark_d2d_gemini(bits, scheme) for _ in range(iterations)]
            
            # Average
            def avg_results(results):
                valid = [r for r in results if not r.error]
                if not valid:
                    return results[0]
                avg = BenchmarkResult(results[0].name)
                avg.encode_time = sum(r.encode_time for r in valid) / len(valid)
                avg.decode_time = sum(r.decode_time for r in valid) / len(valid)
                avg.total_time = sum(r.total_time for r in valid) / len(valid)
                avg.encode_memory = sum(r.encode_memory for r in valid) / len(valid)
                avg.decode_memory = sum(r.decode_memory for r in valid) / len(valid)
                avg.total_memory = sum(r.total_memory for r in valid) / len(valid)
                return avg
            
            avg_user = avg_results(user_results)
            avg_claude = avg_results(claude_results)
            avg_gemini = avg_results(gemini_results)
            
            print(f"    {format_result(avg_user)}")
            print(f"    {format_result(avg_claude)}")
            print(f"    {format_result(avg_gemini)}")

            # Store in CSV Data
            for r in [avg_user, avg_claude, avg_gemini]:
                csv_data.append({
                    "Mode": "D2D",
                    "Scheme": scheme,
                    "Test/Signal": test_name,
                    "Implementation": r.name,
                    "Encode Time (ms)": r.encode_time * 1000,
                    "Decode Time (ms)": r.decode_time * 1000,
                    "Total Time (ms)": r.total_time * 1000,
                    "Encode Memory (KB)": r.encode_memory / 1024,
                    "Decode Memory (KB)": r.decode_memory / 1024,
                    "Total Memory (KB)": r.total_memory / 1024
                })
            
            # Winner
            if not avg_claude.error and not avg_gemini.error:
                if avg_claude.total_time < avg_gemini.total_time:
                    print(f"    🏆 Claude wins: {avg_gemini.total_time/avg_claude.total_time:.2f}x faster")
                else:
                    print(f"    🏆 Gemini wins: {avg_claude.total_time/avg_gemini.total_time:.2f}x faster")
    
    # ========== MODE 2: DIGITAL-TO-ANALOG ==========
    print("\n" + "=" * 100)
    print("MODE 2: DIGITAL-TO-ANALOG (D2A)")
    print("=" * 100)
    
    d2a_schemes = ["ask", "fsk", "bpsk"]
    
    for scheme in d2a_schemes:
        print(f"\n--- Scheme: {scheme.upper()} ---")
        
        for test_name, bits in test_cases.items():
            print(f"\n  Test: {test_name}")
            
            user_results = [benchmark_d2a_user(bits, scheme) for _ in range(iterations)]
            claude_results = [benchmark_d2a_claude(bits, scheme) for _ in range(iterations)]
            gemini_results = [benchmark_d2a_gemini(bits, scheme) for _ in range(iterations)]
            
            def avg_results(results):
                valid = [r for r in results if not r.error]
                if not valid:
                    return results[0]
                avg = BenchmarkResult(results[0].name)
                avg.encode_time = sum(r.encode_time for r in valid) / len(valid)
                avg.decode_time = sum(r.decode_time for r in valid) / len(valid)
                avg.total_time = sum(r.total_time for r in valid) / len(valid)
                avg.encode_memory = sum(r.encode_memory for r in valid) / len(valid)
                avg.decode_memory = sum(r.decode_memory for r in valid) / len(valid)
                avg.total_memory = sum(r.total_memory for r in valid) / len(valid)
                return avg
            
            avg_user = avg_results(user_results)
            avg_claude = avg_results(claude_results)
            avg_gemini = avg_results(gemini_results)
            
            print(f"    {format_result(avg_user)}")
            print(f"    {format_result(avg_claude)}")
            print(f"    {format_result(avg_gemini)}")
            
            # Store in CSV Data
            for r in [avg_user, avg_claude, avg_gemini]:
                csv_data.append({
                    "Mode": "D2A",
                    "Scheme": scheme,
                    "Test/Signal": test_name,
                    "Implementation": r.name,
                    "Encode Time (ms)": r.encode_time * 1000,
                    "Decode Time (ms)": r.decode_time * 1000,
                    "Total Time (ms)": r.total_time * 1000,
                    "Encode Memory (KB)": r.encode_memory / 1024,
                    "Decode Memory (KB)": r.decode_memory / 1024,
                    "Total Memory (KB)": r.total_memory / 1024
                })

            if not avg_claude.error and not avg_gemini.error:
                if avg_claude.total_time < avg_gemini.total_time:
                    print(f"    🏆 Claude wins: {avg_gemini.total_time/avg_claude.total_time:.2f}x faster")
                else:
                    print(f"    🏆 Gemini wins: {avg_claude.total_time/avg_gemini.total_time:.2f}x faster")
    
    # ========== MODE 3: ANALOG-TO-DIGITAL ==========
    print("\n" + "=" * 100)
    print("MODE 3: ANALOG-TO-DIGITAL (A2D) - PCM")
    print("=" * 100)
    
    signal_lengths = [500, 1000, 2000]
    
    for sig_len in signal_lengths:
        print(f"\n  Signal Length: {sig_len} samples")
        
        user_results = [benchmark_a2d_user(sig_len) for _ in range(iterations)]
        claude_results = [benchmark_a2d_claude(sig_len) for _ in range(iterations)]
        gemini_results = [benchmark_a2d_gemini(sig_len) for _ in range(iterations)]
        
        def avg_results(results):
            valid = [r for r in results if not r.error]
            if not valid:
                return results[0]
            avg = BenchmarkResult(results[0].name)
            avg.encode_time = sum(r.encode_time for r in valid) / len(valid)
            avg.decode_time = sum(r.decode_time for r in valid) / len(valid)
            avg.total_time = sum(r.total_time for r in valid) / len(valid)
            avg.encode_memory = sum(r.encode_memory for r in valid) / len(valid)
            avg.decode_memory = sum(r.decode_memory for r in valid) / len(valid)
            avg.total_memory = sum(r.total_memory for r in valid) / len(valid)
            return avg
        
        avg_user = avg_results(user_results)
        avg_claude = avg_results(claude_results)
        avg_gemini = avg_results(gemini_results)
        
        print(f"    {format_result(avg_user)}")
        print(f"    {format_result(avg_claude)}")
        print(f"    {format_result(avg_gemini)}")
        
        # Store in CSV Data
        for r in [avg_user, avg_claude, avg_gemini]:
            csv_data.append({
                "Mode": "A2D",
                "Scheme": "PCM",
                "Test/Signal": f"{sig_len} samples",
                "Implementation": r.name,
                "Encode Time (ms)": r.encode_time * 1000,
                "Decode Time (ms)": r.decode_time * 1000,
                "Total Time (ms)": r.total_time * 1000,
                "Encode Memory (KB)": r.encode_memory / 1024,
                "Decode Memory (KB)": r.decode_memory / 1024,
                "Total Memory (KB)": r.total_memory / 1024
            })

        if not avg_claude.error and not avg_gemini.error:
            if avg_claude.total_time < avg_gemini.total_time:
                print(f"    🏆 Claude wins: {avg_gemini.total_time/avg_claude.total_time:.2f}x faster")
            else:
                print(f"    🏆 Gemini wins: {avg_claude.total_time/avg_gemini.total_time:.2f}x faster")
    
    # ========== MODE 4: ANALOG-TO-ANALOG ==========
    print("\n" + "=" * 100)
    print("MODE 4: ANALOG-TO-ANALOG (A2A) - AM Modulation")
    print("=" * 100)
    
    signal_lengths = [500, 1000, 2000]
    
    for sig_len in signal_lengths:
        print(f"\n  Signal Length: {sig_len} samples")
        
        user_results = [benchmark_a2a_user(sig_len) for _ in range(iterations)]
        claude_results = [benchmark_a2a_claude(sig_len) for _ in range(iterations)]
        gemini_results = [benchmark_a2a_gemini(sig_len) for _ in range(iterations)]
        
        def avg_results(results):
            valid = [r for r in results if not r.error]
            if not valid:
                return results[0]
            avg = BenchmarkResult(results[0].name)
            avg.encode_time = sum(r.encode_time for r in valid) / len(valid)
            avg.decode_time = sum(r.decode_time for r in valid) / len(valid)
            avg.total_time = sum(r.total_time for r in valid) / len(valid)
            avg.encode_memory = sum(r.encode_memory for r in valid) / len(valid)
            avg.decode_memory = sum(r.decode_memory for r in valid) / len(valid)
            avg.total_memory = sum(r.total_memory for r in valid) / len(valid)
            return avg
        
        avg_user = avg_results(user_results)
        avg_claude = avg_results(claude_results)
        avg_gemini = avg_results(gemini_results)
        
        print(f"    {format_result(avg_user)}")
        print(f"    {format_result(avg_claude)}")
        print(f"    {format_result(avg_gemini)}")
        
        # Store in CSV Data
        for r in [avg_user, avg_claude, avg_gemini]:
            csv_data.append({
                "Mode": "A2A",
                "Scheme": "AM",
                "Test/Signal": f"{sig_len} samples",
                "Implementation": r.name,
                "Encode Time (ms)": r.encode_time * 1000,
                "Decode Time (ms)": r.decode_time * 1000,
                "Total Time (ms)": r.total_time * 1000,
                "Encode Memory (KB)": r.encode_memory / 1024,
                "Decode Memory (KB)": r.decode_memory / 1024,
                "Total Memory (KB)": r.total_memory / 1024
            })

        if not avg_claude.error and not avg_gemini.error:
            if avg_claude.total_time < avg_gemini.total_time:
                print(f"    🏆 Claude wins: {avg_gemini.total_time/avg_claude.total_time:.2f}x faster")
            else:
                print(f"    🏆 Gemini wins: {avg_claude.total_time/avg_gemini.total_time:.2f}x faster")
    
    print("\n" + "=" * 100)
    print("BENCHMARK COMPLETE!")
    print("=" * 100)

    # Save to CSV
    csv_filename = "benchmark_results.csv"
    try:
        keys = csv_data[0].keys()
        with open(csv_filename, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(csv_data)
        print(f"Results saved to {csv_filename}")
    except Exception as e:
        print(f"Failed to save CSV: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive benchmark for all 4 communication modes")
    parser.add_argument('--bits', type=int, default=256, help='Bit length for digital tests')
    parser.add_argument('--iterations', type=int, default=30, help='Iterations per test')
    
    args = parser.parse_args()
    
    run_comprehensive_benchmark(bit_length=args.bits, iterations=args.iterations)
