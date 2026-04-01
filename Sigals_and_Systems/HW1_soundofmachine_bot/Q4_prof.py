import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import soundfile as sf

# Read audio
fs, x = wavfile.read("ilberortayli.wav")
if len(x.shape) > 1:
    x = x[:, 0]

x = x.astype(np.float32)

def apply_system(x):
    A = np.zeros_like(x)
    y = np.zeros_like(x)

    for n in range(len(x)):
        A_prev1 = A[n-1] if n-1 >= 0 else 0
        A_prev2 = A[n-2] if n-2 >= 0 else 0
        A[n] = x[n] + 1.5 * A_prev1 - 0.5 * A_prev2

        A_prev1 = A[n-1] if n-1 >= 0 else 0
        y[n] = 0.75 * A[n] + 0.25 * A_prev1

    y = np.nan_to_num(y, nan=-1.0)
    return y

# original
x_raw = x.copy()

# 1x 
y_once = apply_system(x_raw)

# 5x 
y_five = x_raw.copy()
for _ in range(5):
    y_five = apply_system(y_five)

# 100x 
y_hundred = x_raw.copy()
for _ in range(100):
    y_hundred = apply_system(y_hundred)

#save raw
sf.write("output_once.wav", y_once, fs)
sf.write("output_five.wav", y_five, fs)
sf.write("output_hundred.wav", y_hundred, fs)

t = np.arange(len(x)) / fs

# Normalize signals for plotting
def normalize_for_plot(signal):
    max_val = np.max(np.abs(signal))
    return signal / max_val if max_val != 0 else signal

plt.figure(figsize=(12, 6))
plt.plot(t, normalize_for_plot(x_raw), label="Original", alpha=0.7)
plt.plot(t, normalize_for_plot(y_once), label="1x System", alpha=0.7)
plt.plot(t, normalize_for_plot(y_five), label="5x System", alpha=0.7)
plt.plot(t, normalize_for_plot(y_hundred), label="100x System", alpha=0.7)
plt.xlabel("Time [s]")
plt.ylabel("Normalized Amplitude")
plt.title("Original vs Processed Signals (Plotted with Normalization)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
