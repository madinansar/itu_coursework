import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.fft import rfft, rfftfreq

fs_voice, voice = wavfile.read("sep_voice.wav")
fs_instrument, instrument = wavfile.read("sep_instrument.wav")

min_length = min(len(voice), len(instrument))

voice = voice[:min_length] / np.max(np.abs(voice))  # normalize 
instrument = instrument[:min_length] / np.max(np.abs(instrument)) 

new_mixed = voice + instrument

new_mixed = np.int16(new_mixed / np.max(np.abs(new_mixed)) * 32767)
wavfile.write("new_mixed.wav", fs_voice, new_mixed)

def plot_all_spectra_and_time(mixed, combined, voice, instrument, fs):
    plt.figure(figsize=(14, 12))

    signals = [mixed, combined, voice, instrument]
    titles = ["Original Mixed Signal", "Combined Signal", "Separated Voice", "Separated Instrument"]

    for i, (signal, title) in enumerate(zip(signals, titles)):
        n = len(signal)
        time = np.linspace(0, n / fs, n)
        freqs = rfftfreq(n, d=1/fs)
        fft_values = np.abs(rfft(signal))

        plt.subplot(4, 2, i * 2 + 1)
        plt.plot(time, signal, color='#E0218A')
        plt.title(f"{title} (Time Domain)")
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.xlim(0, 0.03)  
        plt.grid(True)

        plt.subplot(4, 2, i * 2 + 2)
        plt.plot(freqs, fft_values, color='#E0218A')
        plt.title(f"{title} (Frequency Domain)")
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Magnitude")
        plt.xlim(0, 1000)  
        plt.grid(True)

    plt.tight_layout()
    plt.show()

fs_mixed, original_mixed = wavfile.read("mixed_q1.wav")

plot_all_spectra_and_time(original_mixed, new_mixed, voice, instrument, fs_voice)
