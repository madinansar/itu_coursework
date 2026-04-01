# BLG354E HW2 - DFT and Signal Classification

Short code solutions for HW2 signal processing tasks.

## Contents

- question1.py
  - Separates mixed audio into voice and instrument using FFT band-pass filtering.
  - Inputs: mixed_q1.wav
  - Outputs: sep_voice.wav, sep_instrument.wav

- question2.py
  - Recombines separated signals and compares original vs combined signal in time/frequency domain.
  - Inputs: mixed_q1.wav, sep_voice.wav, sep_instrument.wav
  - Output: new_mixed.wav

- question3.py
  - Classifies sample waveforms (sine/square/triangle) using simple DFT feature distance.
  - Uses reference signals in prototype_signals_q3/ and test samples in signals_q3/.

## Run

```bash
python question1.py
python question2.py
python question3.py
```

Assignment files: BLG354E_HW2.pdf,
See Report for details: signals_hw2.pdf.
