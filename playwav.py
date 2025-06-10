#!/usr/bin/env python3
"""
playwav.py - Play a .wav file using Adafruit Speaker Bonnet (I2S audio) on Raspberry Pi.
Usage: python playwav.py <filename.wav>
"""
import sys
import time
import pygame

volume_level = 0.02 

if len(sys.argv) != 2:
    print("Usage: python playwav.py <filename.wav>")
    sys.exit(1)

wav_file = sys.argv[1]

pygame.mixer.init()
try:
    pygame.mixer.music.load(wav_file)
    pygame.mixer.music.set_volume(volume_level)  # Set volume
    pygame.mixer.music.play()
    print(f"Playing: {wav_file} at {int(volume_level * 100)}% volume")
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
except Exception as e:
    print(f"Error playing {wav_file}: {e}")
    sys.exit(1)
finally:
    pygame.mixer.music.stop()
    pygame.mixer.quit()
