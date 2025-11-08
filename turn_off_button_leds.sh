#!/bin/sh
# Simple wrapper to run the Python LED-off script. Use this in cron or systemd.
PYTHON=/usr/bin/python3
SCRIPT_DIR="/home/pi/Alarm-Clock-v2"
$PYTHON "$SCRIPT_DIR/turn_off_button_leds.py" >/var/log/turn_off_button_leds.log 2>&1
