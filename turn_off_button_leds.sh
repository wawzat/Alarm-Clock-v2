#!/bin/sh
# Simple wrapper to run the Python LED-off script. Use this in cron or systemd.
# Writes logs to the calling user's home directory to avoid permission errors
# when running from cron as a non-root user.
PYTHON=/usr/bin/python3
SCRIPT_DIR="/home/pi/Alarm-Clock-v2"
LOG_DIR="/home/pi"
LOG_FILE="$LOG_DIR/turn_off_button_leds.log"

# If the default home path doesn't exist or is not writable, fall back to
# writing to stdout (cron will capture stdout/stderr). This avoids permission
# denied errors when trying to write to /var/log.
if [ -w "$LOG_DIR" ] || ( [ ! -e "$LOG_FILE" ] && [ -w "$LOG_DIR" ] ); then
	$PYTHON "$SCRIPT_DIR/turn_off_button_leds.py" >"$LOG_FILE" 2>&1
else
	$PYTHON "$SCRIPT_DIR/turn_off_button_leds.py"
fi
