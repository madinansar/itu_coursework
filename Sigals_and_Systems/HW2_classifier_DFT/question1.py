import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import butter, lfilter

def fft_bandpass_filter(signal, fs, lowcut, highcut):
    n = len(signal)
    freq = np.fft.rfftfreq(n, d=1/fs)
    spectrum = np.fft.rfft(signal)

    mask = (freq >= lowcut) & (freq <= highcut)
    filtered_spectrum = np.where(mask, spectrum, 0)

    filtered_signal = np.fft.irfft(filtered_spectrum, n=n)
    return filtered_signal

fs, mixed = wavfile.read("mixed_q1.wav")

voice = fft_bandpass_filter(mixed, fs, 100, 250)
instrument = fft_bandpass_filter(mixed, fs, 600, 900)

def to_int16(sig):
    return np.int16(sig / np.max(np.abs(sig)) * 32767)

wavfile.write("sep_voice.wav", fs, to_int16(voice))
wavfile.write("sep_instrument.wav", fs, to_int16(instrument))

def plot_time_freq(mixed, voice, instrument, fs):
    plt.figure(figsize=(16, 12))

    signals = [mixed, voice, instrument]
    titles = ["Original Mixed Signal", "Separated Voice (FFT)", "Separated Instrument (FFT)"]

    for i, (signal, title) in enumerate(zip(signals, titles)):
        n = len(signal)
        time = np.linspace(0, n / fs, n)
        freqs = np.fft.rfftfreq(n, d=1/fs)
        fft_values = np.abs(np.fft.rfft(signal))

        #Time Domain Plot
        plt.subplot(3, 2, i * 2 + 1)
        plt.plot(time, signal, color='#E0218A')
        plt.title(f"{title} - Time Domain")
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.grid(True)
        plt.xlim(0, 0.03)  

        #Frequency Domain Plot
        plt.subplot(3, 2, i * 2 + 2)
        markerline, stemlines, baseline = plt.stem(freqs, fft_values, basefmt=" ", linefmt='#E0218A', markerfmt=' ')
        plt.title(f"{title} - Frequency Domain")
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Magnitude")
        plt.xlim(0, 1000)  
        plt.grid(True)

    plt.tight_layout()
    plt.show()

plot_time_freq(mixed, voice, instrument, fs)

