import numpy as np
import matplotlib.pyplot as plt
import scipy.io.wavfile as wav
from scipy.io import wavfile
from scipy.signal import butter, lfilter

def DFT(x, N):
    x = x[:N]
    n = np.arange(N)
    k = n.reshape((N, 1))
    W = np.exp(-2j * np.pi * k * n / N)
    return np.dot(W, x)

def normalize(x):
    return x.astype(np.float32) / np.max(np.abs(x))

def compute_dft_features(signal, N_values=[4, 8]):
    return np.concatenate([np.abs(DFT(signal, N)) for N in N_values])

ref_signals = {}
for name in ['sine', 'square', 'triangle']:
    sr, sig = wavfile.read(f"prototype_signals_q3/{name}.wav")
    ref_signals[name] = normalize(sig)


ref_features = {} 
for name, sig in ref_signals.items():
    features = compute_dft_features(sig)  
    ref_features[name] = features


def classify_signal_from_data(signal):
    signal = normalize(signal)
    unknown_feat = compute_dft_features(signal)
    distances = {
        name: np.linalg.norm(unknown_feat - feat)
        for name, feat in ref_features.items()
    }
    prediction = min(distances, key=distances.get)
    return prediction, distances


sample_signals = {}
predictions = []

for i in range(1, 13):
    name = str(i)
    sr, sig = wavfile.read(f"signals_q3/sample_{name}.wav")
    signal = normalize(sig)
    sample_signals[name] = signal
    pred, dist = classify_signal_from_data(signal)
    predictions.append((name, pred, dist))


print("=== Classifications for 12 Samples ===")
for name, pred, dist in predictions:
    print(f"Sample {name} is {pred} wave, Distances = {dist}")


N_values = [4, 8]
fig, axs = plt.subplots(4, 6, figsize=(18, 10))
names = list(sample_signals.keys())

for idx, name in enumerate(names):
    signal = sample_signals[name]
    for i, N in enumerate(N_values):
        plot_idx = idx * 2 + i  
        row = plot_idx // 6
        col = plot_idx % 6
        ax = axs[row, col]
        X = DFT(signal, N)
        markerline, stemlines, baseline = ax.stem(np.abs(X))
        plt.setp(markerline, color='#E0218A')   
        plt.setp(stemlines, color='#E0218A')     
        ax.set_title(f"Sample {name} - {N}-point DFT")
        ax.set_xlabel("Frequency Bin")
        ax.set_ylabel("Magnitude")
        ax.grid(True)

plt.tight_layout()
plt.show()


