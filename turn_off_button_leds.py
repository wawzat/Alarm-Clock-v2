#!/usr/bin/env python3
"""
turn_off_button_leds.py

Simple script to switch off the Adafruit 1x4 arcade button LEDs by setting
their PWM duty cycle to 0. Intended to be run at boot (for example via cron
with @reboot).
"""

import time
import board
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.pwmout import PWMOut

ARCADE_BUTTON_ADDR = 0x3A
LED_PINS = (12, 13)


def turn_off_leds():
    try:
        # Initialize I2C and the seesaw device
        i2c = board.I2C()
        arcade = Seesaw(i2c, addr=ARCADE_BUTTON_ADDR)

        # Create PWM outputs for each LED pin and set to 0
        leds = [PWMOut(arcade, pin) for pin in LED_PINS]
        for led in leds:
            led.duty_cycle = 0

        # short pause to let hardware settle
        time.sleep(0.1)
        return 0
    except Exception as exc:
        # Print the exception to stdout/stderr so the caller can log it
        print("turn_off_button_leds: failed to set LEDs to 0:", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(turn_off_leds())
