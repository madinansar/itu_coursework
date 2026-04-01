import soundcard as sc
import numpy as np
import pyautogui
import time
import random

MOVE_DURATION = 0.2  
INTENSITY_THRESHOLD = 0.00001 

mics = sc.all_microphones(include_loopback=True)
default_mic = mics[1]  

prev_intensity = 0  
curr_intensity = 0  

def move_character(direction):
    """Simulates key presses based on audio direction."""
    print(f"Moving: {direction}")  # Log the direction to terminal

    if direction == "left":
        pyautogui.keyDown('a')
        time.sleep(MOVE_DURATION)
        pyautogui.keyUp('a')
    elif direction == "right":
        pyautogui.keyDown('d')
        time.sleep(MOVE_DURATION)
        pyautogui.keyUp('d')
    elif direction == "forward":
        pyautogui.keyDown('w')
        time.sleep(MOVE_DURATION)
        pyautogui.keyUp('w')
    elif direction == "backward":
        pyautogui.keyDown('s')
        time.sleep(MOVE_DURATION)
        pyautogui.keyUp('s')
    time.sleep(0.1)

def get_intensity():
    """Get the latest intensity from the microphone."""
    with default_mic.recorder(samplerate=48000) as mic:
        data = mic.record(numframes=1024)
        intensity = np.abs(data).mean(axis=0)
    return intensity[0]  

print("Starting...")
time.sleep(3)  

# Get initial intensity
prev_intensity = get_intensity()

while True:
    print("Starting horizontal movement (right)...")
    horizontal_direction = "right"
    
    # Horizontal movement loop
    curr_intensity = get_intensity()

    while curr_intensity > prev_intensity:
        move_character(horizontal_direction)
        consecutive_hor = 0 
        prev_intensity=curr_intensity
        curr_intensity = get_intensity()
        
        if curr_intensity < prev_intensity:  # Intensity decreased
            print(f"Intensity decreased. Switching to left...")  # Log intensity decrease and direction switch
            horizontal_direction = "left"
            move_character(horizontal_direction)
            prev_intensity=curr_intensity
            curr_intensity = get_intensity()
            consecutive_hor += 1

            if consecutive_hor >= 2:
                    print(f"Too many consecutive backward movements. Stopping.")
                    break
        
    
    # Vertical movement loop
    print("Starting vertical movement (forward)...")
    vertical_direction = "forward"

    consecutive_vert = 0 
    prev_intensity = curr_intensity
    curr_intensity = get_intensity()

    while curr_intensity > prev_intensity:
        move_character(vertical_direction)
        prev_intensity=curr_intensity
        curr_intensity = get_intensity()
        
        if curr_intensity < prev_intensity:  # Intensity decreased
            print(f"Intensity decreased. Switching to backward...")  # Log intensity decrease and direction switch
            vertical_direction = "backward"
            move_character(vertical_direction)
            prev_intensity=curr_intensity
            curr_intensity = get_intensity()
            consecutive_vert += 1
        
            if consecutive_vert >= 2:
                    print(f"Too many consecutive backward movements. Stopping.")
                    break


        
