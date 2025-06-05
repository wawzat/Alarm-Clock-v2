import time
import board
import digitalio
from adafruit_seesaw.digitalio import DigitalIO
from adafruit_seesaw.pwmout import PWMOut
from adafruit_seesaw.seesaw import Seesaw

# I2C address for Adafruit LED Arcade Button 1x4
ARCADE_BUTTON_ADDR = 0x3A
# Button pins: 18 (yellow), 19 (white)
BUTTON_PINS = (18, 19)
LED_PINS = (12, 13)  # Per Adafruit example: 12 (yellow), 13 (white)

# Set up I2C and Seesaw device
i2c = board.I2C()  # uses board.SCL and board.SDA
arcade = Seesaw(i2c, addr=ARCADE_BUTTON_ADDR)

# Set up digitalio for buttons
buttons = []
for pin in BUTTON_PINS:
    button = DigitalIO(arcade, pin)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    buttons.append(button)

# Set up PWMOut for LEDs
leds = [PWMOut(arcade, pin) for pin in LED_PINS]

print("Press the yellow or white arcade button (Ctrl+C to exit)...")

try:
    while True:
        for idx, button in enumerate(buttons):
            if not button.value:  # Button is active low
                if idx == 0:
                    print("Yellow button pressed")
                elif idx == 1:
                    print("white button pressed")
                # Pulse the LED while pressed
                for cycle in range(0, 65535, 8000):
                    leds[idx].duty_cycle = cycle
                    time.sleep(0.005)
                for cycle in range(65534, 0, -8000):
                    leds[idx].duty_cycle = cycle
                    time.sleep(0.005)
            else:
                leds[idx].duty_cycle = 0
        time.sleep(0.01)
except KeyboardInterrupt:
    print("\nExiting...")
    for led in leds:
        led.duty_cycle = 0
