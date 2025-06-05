import time
import board
import busio
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw import digitalio

# I2C address for Adafruit LED Arcade Button 1x4
ARCADE_BUTTON_ADDR = 0x3A
# Button pins: 18 (yellow), 19 (white), 20, 2
BUTTON_PINS = [18, 19]
LED_PINS = [14, 15]

# Set up I2C and Seesaw device
i2c = busio.I2C(board.SCL, board.SDA)
arcade = Seesaw(i2c, addr=ARCADE_BUTTON_ADDR)

# Set up digitalio for buttons and LEDs
buttons = [digitalio.DigitalIO(arcade, pin) for pin in BUTTON_PINS]
leds = [digitalio.DigitalIO(arcade, pin) for pin in LED_PINS]

# Set LED pins as outputs and turn off initially
for led in leds:
    led.direction = 1  # output
    led.value = False

# Track last button state for edge detection
last_button_states = [btn.value for btn in buttons]

print("Press the yellow or white arcade button (Ctrl+C to exit)...")

try:
    while True:
        for idx, btn in enumerate(buttons):
            current = btn.value
            last = last_button_states[idx]
            # Button is active low: pressed == False
            if not current and last:  # Button down event
                if idx == 0:
                    print("Yellow button pressed")
                    leds[0].value = True
                elif idx == 1:
                    print("white button pressed")
                    leds[1].value = True
            elif current and not last:  # Button up event
                leds[idx].value = False
            last_button_states[idx] = current
        time.sleep(0.01)
except KeyboardInterrupt:
    print("\nExiting...")
    for led in leds:
        led.value = False
