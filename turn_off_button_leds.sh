#!/bin/sh
# Simple wrapper to run the Python LED-off script. Use this in cron or systemd.
# Writes logs to the calling user's home directory to avoid permission errors
# when running from cron as a non-root user.
SCRIPT_DIR="/home/pi/Alarm-Clock-v2"
# Prefer a virtualenv python inside the repository if present. Common names
# include: .venv, venv, env, .env. The script looks for a python executable in
# these venvs and falls back to /usr/bin/python3.
PYTHON="/usr/bin/python3"
for cand in ".venv" "venv" "env" ".env"; do
	if [ -x "$SCRIPT_DIR/$cand/bin/python" ]; then
		PYTHON="$SCRIPT_DIR/$cand/bin/python"
		break
	fi
done

LOG_DIR="/home/pi"
LOG_FILE="$LOG_DIR/turn_off_button_leds.log"

# If the default home path doesn't exist or is not writable, fall back to
# writing to stdout (cron will capture stdout/stderr). This avoids permission
# denied errors when trying to write to /var/log.
if [ -w "$LOG_DIR" ] || ( [ ! -e "$LOG_FILE" ] && [ -w "$LOG_DIR" ] ); then
	"$PYTHON" "$SCRIPT_DIR/turn_off_button_leds.py" >"$LOG_FILE" 2>&1
else
	"$PYTHON" "$SCRIPT_DIR/turn_off_button_leds.py"
fi
