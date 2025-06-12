# wave.py
# Detects left-to-right and right-to-left gestures using the Adafruit APDS9960 sensor
# Prints the gesture direction to the terminal
# This program was used to test the APDS9960 sensor for wave detection.
# It is stand-alone and not required by aclock.py.

import time
import board
import busio
from adafruit_apds9960.apds9960 import APDS9960

# Initialize I2C bus and APDS9960 sensor
i2c = busio.I2C(board.SCL, board.SDA)
apds = APDS9960(i2c)
apds.enable_proximity = True
apds.enable_gesture = True

print("Wave detection started. Perform a left-to-right or right-to-left gesture.")

try:
    while True:
        gesture = apds.gesture()
        if gesture == 0x01:  # Up
            pass
        elif gesture == 0x02:  # Down
            pass
        elif gesture == 0x03:  # Left
            print("Right to left")
        elif gesture == 0x04:  # Right
            print("Left to right")
        time.sleep(0.05)
except KeyboardInterrupt:
    print("\nExiting wave detection.")
