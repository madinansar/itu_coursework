# BLG354E HW1 - Sound-Based Machine Bot

This folder contains code solutions for HW1 code tasks (Q3 and Q4) in Signals and Systems.

## Files in Folder

- q3.py
  - Sound-controlled game bot.
  - Captures loopback audio intensity and moves with WASD toward higher sound level.
  - Uses a step-and-compare strategy on horizontal then vertical directions.

- q3_while.py
  - Alternative iterative version of the Q3 bot.
  - Continuously measures intensity and switches movement direction when intensity drops.

- Q4_prof.py
  - Audio processing task for a recursive discrete-time system.
  - Reads an input WAV file, applies the system 1x, 5x, and 100x, and saves:
    - output_once.wav
    - output_five.wav
    - output_hundred.wav
  - Also plots normalized original vs processed waveforms.


- BLG354E__HW1_2025-1-2.pdf: homework statement.
- output_once.wav, output_five.wav, output_hundred.wav: generated outputs from Q4.

## Dependencies

Install required libraries in your environment:

```bash
pip install numpy matplotlib scipy soundfile soundcard pyautogui
```

## How to Run

Run Q3 bot:

```bash
python q3.py
```

Alternative Q3 version:

```bash
python q3_while.py
```

Run Q4 audio system script:

```bash
python Q4_prof.py
```

Note: Q3 scripts use keyboard automation and loopback microphone capture, so they should be run carefully while the target game/app is focused.
