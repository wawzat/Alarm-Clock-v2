Turn off button LEDs at boot

This repository includes a small script, `turn_off_button_leds.py`, which
initializes the Adafruit Seesaw device used by the arcade buttons and sets
their PWM duty cycle to 0 (turns LEDs off). To run this script automatically
when the Raspberry Pi boots, add a cron job for the pi user (or the user that
runs your alarm clock):

Example crontab entry (edit with `crontab -e`):

@reboot /usr/bin/python3 /home/pi/Alarm-Clock-v2/turn_off_button_leds.py >/home/pi/turn_off_button_leds.log 2>&1

Notes:
- Adjust the path to the repository above to match where you placed it on the
  Raspberry Pi (the example assumes `/home/pi/Alarm-Clock-v2`).
- The script depends on the `adafruit_seesaw` library; ensure your Pi has the
  project's dependencies installed (see `requirements.txt`).
- If you'd prefer a systemd service instead of cron, create a small unit that
  runs the script at boot and enable it; this can be more reliable on some
  systems.
