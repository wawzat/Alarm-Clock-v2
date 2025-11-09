Turn off button LEDs at boot

This repository includes a small script, `turn_off_button_leds.py`, which
initializes the Adafruit Seesaw device used by the arcade buttons and sets
their PWM duty cycle to 0 (turns LEDs off). To run this script automatically
when the Raspberry Pi boots, add a cron job for the pi user (or the user that
runs your alarm clock):

Example crontab entry (edit with `crontab -e`):

@reboot /home/pi/Alarm-Clock-v2/turn_off_button_leds.sh >/home/pi/turn_off_button_leds.log 2>&1

Notes:
- Adjust the path to the repository above to match where you placed it on the
  Raspberry Pi (the example assumes `/home/pi/Alarm-Clock-v2`).
- The script depends on the `adafruit_seesaw` library; ensure your Pi has the
  project's dependencies installed (see `requirements.txt`).
- If you'd prefer a systemd service instead of cron, create a small unit that
  runs the script at boot and enable it; this can be more reliable on some
  systems.

Notes about the wrapper script

- The repo contains a small wrapper `turn_off_button_leds.sh` that executes the
  Python script and sends logs to `/var/log`. Make the wrapper executable after
  you copy the repository to the Pi:

  chmod +x /home/pi/Alarm-Clock-v2/turn_off_button_leds.sh

- The wrapper uses `/usr/bin/python3` and assumes the repository is at
  `/home/pi/Alarm-Clock-v2`; update the paths in the `.sh` file if your layout
  differs.

Virtual environment support

- If you installed the project's Python dependencies into a virtual
  environment inside the repository (recommended), the wrapper will attempt
  to use that venv's Python automatically. It looks for Python at these
  locations inside the repo (in order): `.venv/bin/python`, `venv/bin/python`,
  `env/bin/python`, `.env/bin/python`.

- To create and use a venv inside the repo on the Pi, run (from the repo root):

  python3 -m venv .venv
  . .venv/bin/activate
  pip install -r requirements.txt

  Then make the wrapper executable and add the cron entry as shown above.
