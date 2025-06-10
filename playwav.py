#!/usr/bin/env python3
"""
playwav.py - Play a .wav file using Adafruit Speaker Bonnet (I2S audio) on Raspberry Pi.
Usage: python playwav.py <filename.wav>
"""
import sys
import time
import pygame

volume_level = 0.02 

if len(sys.argv) == 2:
    wav_file = sys.argv[1]
    files_to_play = [wav_file]
else:
    files_to_play = [f"{i:02}.mp3" for i in range(1, 7)]

pygame.mixer.init()
try:
    while True:
        for wav_file in files_to_play:
            try:
                pygame.mixer.music.load(wav_file)
                pygame.mixer.music.set_volume(volume_level)  # Set volume
                pygame.mixer.music.play()
                print(f"Playing: {wav_file} at {int(volume_level * 100)}% volume")
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                time.sleep(1)  # 1 second pause between tracks
            except Exception as e:
                print(f"Error playing {wav_file}: {e}")
                continue
except KeyboardInterrupt:
    print("\nPlayback interrupted by user.")
    sys.exit(0)
finally:
    pygame.mixer.music.stop()
    pygame.mixer.quit()
