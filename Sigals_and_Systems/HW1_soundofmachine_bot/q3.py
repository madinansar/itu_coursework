import soundcard as sc
import numpy as np
import pyautogui
import time

def get_audio_level(mic):
    """Captures audio for a short duration and returns the average volume level."""
    with mic.recorder(samplerate=148000) as mic_rec:
        data = mic_rec.record(numframes=5000) #1000000 is too large to wait 
        volume = np.mean(np.abs(data))  # Compute average volume
    return volume

def press_keys(key, duration=0.01):
    """Presses key for a duratiaon."""
    pyautogui.keyDown(key)
    time.sleep(0.001)
    pyautogui.keyUp(key)
    time.sleep(duration)


# Mapping for the opposite directions.
opposite_direction_map = {
    'w': 's',
    's': 'w',
    'a': 'd',
    'd': 'a',
}

def move_towards_sound(mic):
    cur_volume = get_audio_level(mic)    
    #check right volume to learn which way we should move horizontally
    press_keys('d')
    right_volume = get_audio_level(mic) 
    if right_volume > cur_volume:
        dir = 'd'
    else:
        dir = 'a'
    cur_volume = right_volume
    while True:
        press_keys(dir)
        new_volume = get_audio_level(mic)
        if new_volume < cur_volume:  # Sound decreased, go back one step.
            # Get opposite direction key sequence.
            press_keys(opposite_direction_map[dir])
            break
        cur_volume = new_volume   
      
    cur_volume = get_audio_level(mic)    
    #check up volume to learn which way we should move vertically
    press_keys('w')
    up_volume = get_audio_level(mic) 
    if up_volume > cur_volume:
        dir = 'w'
    else:
        dir = 's'
    cur_volume = up_volume
    while True:
        press_keys(dir)
        new_volume = get_audio_level(mic)
        if new_volume < cur_volume:  # Sound decreased, go back one step.
            # Get opposite direction key sequence.
            press_keys(opposite_direction_map[dir])
            break
        cur_volume = new_volume   

def main():
    mics = sc.all_microphones(include_loopback=True)
    default_mic = mics[0]  
    time.sleep(2) #wait 2 seconds to start the game

    pyautogui.keyDown('enter') #start game
    time.sleep(1)
    pyautogui.keyDown('enter')
    print("Starting bot...")
    
    while True:
        move_towards_sound(default_mic)
        
if __name__ == "__main__":
    main()