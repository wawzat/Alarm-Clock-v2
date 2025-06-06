# Alarm clock with LED Display
# James S. Lucas
# Issues and todo: alarm pre-selects, auto alarm repeat, issues with dimLevel 0 line 402 auto time setting conflict with manual off
#   , display override move to display functions? LED blinking when after 8PM
# 20171118
# 20250605

# I2C addresses:
#   0x70 - 14x4 alphanumeric display
#   0x72 - 7x4 numeric display
#   0x36 - Stemma QT rotary encoder
#   0x39 - IR, Proximity & Gesture Sensor
#   0x3A - LED Arcade Button 1x4

import os
import time
import datetime
from datetime import datetime as dt
from adafruit_ht16k33.segments import Seg7x4
from adafruit_ht16k33.segments import Seg14x4
from gpiozero import DigitalInputDevice, DigitalOutputDevice
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw import rotaryio, digitalio
from adafruit_seesaw.digitalio import DigitalIO
from adafruit_seesaw.pwmout import PWMOut
import digitalio
import logging
import board
import busio
import json
from adafruit_apds9960.apds9960 import APDS9960  # Add APDS9960 import

class AlarmClock:
    """
    AlarmClock provides an alarm clock with LED display, rotary encoder controls, and optional audio features.

    Features:
        - Alarm time and status management
        - LED display brightness and override controls
        - Rotary encoder and button input handling
        - Persistent settings storage and loading
        - Optional audio playback for alarm
        - Proximity and Gesture sensor for snooze and display wake
    """
    SETTINGS_FILE = "settings.json"
    PERSISTED_SETTINGS = [
        "alarm_hour", "alarm_minute", "period", "alarm_stat", "alarm_track", "vol_level",
        "manual_dim_level", "auto_dim_level", "auto_dim", "display_mode", "display_override"
    ]

    def __init__(self):
        """
        Initialize the AlarmClock instance, set up hardware interfaces, state variables, and load persisted settings.
        """
        # Set up logger for error logging
        self.logger = logging.getLogger("aclock")
        self.logger.setLevel(logging.ERROR)
        if not self.logger.handlers:
            handler = logging.FileHandler("aclock_error.log")
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # Remove rotary encoder GPIO and rotary_class_jsl
        # Remove all references to DigitalInputDevice, DigitalOutputDevice, Button for alarm/display settings

        self.i2c = busio.I2C(board.SCL, board.SDA)

        # Initialize I2C for Arcade Button 1x4 (address 0x3A)
        # I2C address for Adafruit LED Arcade Button 1x4
        self.last_state = [True, True]  # True means not pressed (pull-up)
        self.last_press = [0, 0]
        self.debounce_time = 0.25  # 250 ms debounce
        self.ARCADE_BUTTON_ADDR = 0x3A
        # Button pins: 18 (yellow), 19 (white)
        self.BUTTON_PINS = (18, 19)
        self.LED_PINS = (12, 13)  # Per Adafruit example: 12 (yellow), 13 (white)

        # Set up I2C and Seesaw device
        self.arcade = Seesaw(self.i2c, addr=self.ARCADE_BUTTON_ADDR)

        # Set up digitalio for buttons
        self.arcade_buttons = []
        for pin in self.BUTTON_PINS:
            self.button = DigitalIO(self.arcade, pin)
            self.button.direction = digitalio.Direction.INPUT
            self.button.pull = digitalio.Pull.UP
            self.arcade_buttons.append(self.button)

        # Define increment for alarm minute adjustment
        self.minute_incr = 1

        # Create display instances (default I2C address (0x70))
        self.alpha_display = Seg14x4(self.i2c)
        self.num_display = Seg7x4(self.i2c, address=0x72)

        # Initialize Stemma QT rotary encoder (default I2C address 0x36)
        self.encoder_seesaw = Seesaw(self.i2c, addr=0x36)
        self.encoder = rotaryio.IncrementalEncoder(self.encoder_seesaw)
        self.encoder_button = DigitalIO(self.encoder_seesaw, 24)
        self.last_encoder_position = self.encoder.position
        self.last_encoder_button = self.encoder_button.value
        self.encoder_button_down = False
        self.encoder_button_up = False

        # Initialize APDS9960 gesture sensor
        self.apds = APDS9960(self.i2c)
        self.apds.enable_proximity = True
        self.apds.enable_gesture = True

        # Set up I2C and Seesaw device
        self.arcade = Seesaw(self.i2c, addr=self.ARCADE_BUTTON_ADDR)

        # Set up digitalio for buttons
        self.arcade_buttons = []
        for pin in self.BUTTON_PINS:
            self.button = DigitalIO(self.arcade, pin)
            self.button.direction = digitalio.Direction.INPUT
            self.button.pull = digitalio.Pull.UP
            self.arcade_buttons.append(self.button)

        # Set up PWMOut for LEDs
        self.arcade_leds = [PWMOut(self.arcade, pin) for pin in self.LED_PINS]

        # Track last button state for edge detection
        self.last_arcade_button_states = [btn.value for btn in self.arcade_buttons]

        # Audio feature flag
        self.use_audio = False  # Set to True to enable audio features
        if self.use_audio:
            import alsaaudio
            self.mixer = alsaaudio.Mixer('PCM')

        # State variables
        self.alarm_settings_state = 1
        self.display_settings_state = 1
        self.display_mode = "MANUAL_DIM"
        self.display_override = "ON"
        self.alarm_hour = 4
        self.alarm_minute = 0
        self.alarm_time = dt.strptime("04:00", "%H:%M")
        self.alarm_set = 1
        self.display_set = 1
        self.alarm_stat = "OFF"
        self.alarm_ringing = 0
        self.sleep_state = "OFF"
        self.period = "AM"
        self.dim_level = 6
        self.auto_dim_level = 0
        self.manual_dim_level = 6
        self.alarm_track = 1
        self.vol_level = 65
        self.alarm_tracks = {1: '01.mp3', 2: '02.mp3', 3: '03.mp3', 4: '04.mp3', 5: '05.mp3', 6: '06.mp3'}
        # self.distance = 0
        self.auto_dim = "ON"
        self.loop_count = 0
        self.debug = "NO"

        # Rotary encoder action dictionaries
        self.clockwise_alarm_actions = {
            1: self.inc_alarm_hour,
            2: self.inc_alarm_minute,
            3: self.toggle_period,
            4: self.toggle_alarm_stat,
            5: self.inc_alarm_track,
            6: self.inc_vol_level
        }
        self.anticlockwise_alarm_actions = {
            1: self.dec_alarm_hour,
            2: self.dec_alarm_minute,
            3: self.dec_period,
            4: self.dec_alarm_stat,
            5: self.dec_alarm_track,
            6: self.dec_vol_level
        }
        self.clockwise_display_actions = {
            1: self.inc_manual_dim_level,
            2: self.toggle_display_override
        }
        self.anticlockwise_display_actions = {
            1: self.dec_manual_dim_level,
            2: self.toggle_display_override
        }

        # Display cache
        self.last_num_message = None
        self.last_num_brightness = None
        self.last_alpha_message = None
        self.last_alpha_brightness = None
        self.last_alpha_type = None

        # Load settings at startup
        self.load_settings()

    def get_time(self):
        """
        Return the current datetime.

        Returns:
            datetime: The current date and time.
        """
        return dt.now()

    def check_alarm(self, now):
        """
        Check if the alarm should ring based on the current time and alarm settings.
        Handles alarm ringing, snooze logic, and audio playback if enabled.

        Args:
            now (datetime): The current datetime to check against the alarm time.
        """
        loop_count = 0
        vol_increase = 0
        time_decrease = 0
        print(f"time: {now.time()} {self.period}  alarm time: {self.alarm_time.time()}")
        if now.strftime("%p") == self.period and now.time() >= self.alarm_time.time() and self.alarm_stat == "ON":
            self.alarm_ringing = 1
            self.sleep_state = "OFF"
            snooze_triggered = False
            snooze_cooldown = 10  # seconds to wait before alarm can re-trigger after snooze
            snooze_time = None
            # --- Flicker reduction: cache last num display value and colon ---
            last_num_message = None
            last_colon = None
            while self.alarm_ringing == 1 and self.alarm_stat == "ON":
                # --- POLL ARCADE BUTTONS DURING ALARM RING ---
                self.poll_arcade_buttons()
                loop_count += 1
                self.alpha_display.fill(0)
                self.alpha_display.print("RING")
                self.alpha_display.show()
                now = self.get_time()
                num_message = int(now.strftime("%I"))*100+int(now.strftime("%M"))
                colon_state = now.second % 2
                # Only update numeric display if value or colon changed
                if (num_message != last_num_message) or (colon_state != last_colon):
                    self.num_display.fill(0)
                    self.num_display.print(num_message)
                    self.num_display.colon = colon_state
                    try:
                        self.num_display.show()
                    except Exception as e:
                        self.logger.error("num_display.show() error: %s", str(e))
                    last_num_message = num_message
                    last_colon = colon_state
                if self.use_audio:
                    if loop_count % 10 == 0 and (self.vol_level + vol_increase) <= 90:
                        vol_increase += 5
                    if loop_count % 10 == 0 and time_decrease <= 2.25:
                        time_decrease += .25
                    self.mixer.setvolume(self.vol_level+vol_increase)
                    os.system(f"mpg123 -q {self.alarm_tracks[self.alarm_track]} &")
                print(f"alarm ring, now: {now.time()} alarm: {self.alarm_time.time()} Count: {loop_count} Vol: {self.vol_level+vol_increase} Ring Time: {3-time_decrease} alarm_ringing: {self.alarm_ringing} sleep_state: {self.sleep_state}")
                # Check gesture sensor for snooze every 0.1s for up to 2 seconds (or less as time_decrease increases)
                snooze_window = max(0.5, 2-time_decrease)  # never less than 0.5s
                start_time = time.time()
                while time.time() - start_time < snooze_window:
                    # --- POLL ARCADE BUTTONS DURING SNOOZE WINDOW ---
                    self.poll_arcade_buttons()
                    gesture = self.apds.gesture()
                    print(f"APDS9960 gesture: {gesture}")
                    # 0x03 = left (right-to-left), 0x04 = right (left-to-right)
                    if gesture in (0x03, 0x04):
                        print("Snooze triggered by hand wave (gesture)!")
                        self.alarm_ringing = 0
                        self.alarm_time = self.alarm_time + datetime.timedelta(minutes=5)  # 5 min snooze
                        self.sleep_state = "ON"
                        snooze_triggered = True
                        snooze_time = time.time()
                        break
                    time.sleep(0.1)
                if snooze_triggered:
                    # Wait for cooldown before allowing alarm to re-trigger
                    print(f"Snooze cooldown for {snooze_cooldown} seconds.")
                    while time.time() - snooze_time < snooze_cooldown:
                        # --- POLL ARCADE BUTTONS DURING SNOOZE COOLDOWN ---
                        self.poll_arcade_buttons()
                        time.sleep(0.2)
                    break
        elif now >= self.alarm_time and self.alarm_stat == "OFF":
            print("alarm mode off")
        return

    def clear_alpha_display(self):
        """
        Clear the alphanumeric display and handle exceptions.
        """
        self.alpha_display.fill(0)
        try:
            self.alpha_display.show()
        except Exception as e:
            self.logger.error("alpha_display.show() error: %s", str(e))

    def alarm_settings_callback(self, channel):
        """
        Handle alarm settings button events, including entering/exiting alarm settings mode and stopping the alarm.

        Args:
            channel: The event channel (should be BUTTONUP for action).
        """
        debug_lines = []
        debug_lines.append(f"alarm_settings_callback called with channel={channel} alarm_state={self.alarm_settings_state}, display_state={self.display_settings_state}, alarm_set={self.alarm_set}")
        # Only act on BUTTONUP (button release)
        # Remove RotaryEncoder.BUTTONUP reference, use 1 for BUTTONUP
        if channel != 1:
            debug_lines.append("alarm_settings_callback: Ignored, not BUTTONUP")
            print("\n".join(debug_lines), end="\n")
            return
        if self.alarm_ringing == 1:
            debug_lines.append("alarm_settings_callback: Stopping alarm ring")
            self.alarm_ringing = 0
            self.alarm_stat = "OFF"
            self.sleep_state = "OFF"
        elif self.alarm_settings_state == 1:
            debug_lines.append("alarm_settings_callback: Entering alarm settings mode")
            self.alarm_settings_state = 2
            self.alarm_set = 1
        elif self.alarm_settings_state == 2:
            debug_lines.append("alarm_settings_callback: Exiting alarm settings mode")
            self.alarm_settings_state = 1
            self.alpha_display.fill(0)
            try:
                self.alpha_display.show()
            except Exception as e:
                self.logger.error("alpha_display.show() error: %s", str(e))
            #time.sleep(.5)
        # Reset display cache to force refresh
        self.last_num_message = None
        self.last_num_brightness = None
        self.last_alpha_message = None
        self.last_alpha_brightness = None
        self.last_alpha_type = None
        debug_lines.append(f"alarm_settings_callback exit: alarm_state={self.alarm_settings_state}, display_state={self.display_settings_state}, alarm_set={self.alarm_set}")
        print("\n".join(debug_lines), end="\n")
        return

    def display_settings_callback(self, channel):
        """
        Handle display settings button events, including entering/exiting display settings mode.

        Args:
            channel: The event channel (should be BUTTONUP for action).
        """
        debug_lines = []
        debug_lines.append(f"display_settings_callback called with channel={channel} display_state={self.display_settings_state}, alarm_set={self.alarm_set}, aux_set={self.display_set}")
        # Only act on BUTTONUP (button release)
        # Remove RotaryEncoder.BUTTONUP reference, use 1 for BUTTONUP
        if channel != 1:
            return
        if self.display_settings_state == 1:
            debug_lines.append("display_settings_callback: Entering display mode")
            self.alarm_settings_state = 1
            if self.alarm_ringing == 1:
                self.alarm_ringing = 0
                self.alarm_stat = "OFF"
                self.sleep_state = "OFF"
            # Always reset display_settings_state and display_set when entering display settings
            self.display_settings_state = 2
            self.display_set = 1
            self.clear_alpha_display()  # Clear display when entering display mode
            self.save_settings()
            # Reset display cache to force refresh
            self.last_num_message = None
            self.last_num_brightness = None
            self.last_alpha_message = None
            self.last_alpha_brightness = None
            self.last_alpha_type = None
            debug_lines.append(f"display_settings_callback exit: display_state={self.display_settings_state}, alarm_set={self.alarm_set}, aux_set={self.display_set}")
            print("\n".join(debug_lines), end="\n")
            return
        elif self.display_settings_state == 2:
            debug_lines.append("display_settings_callback: Exiting display mode")
            self.display_settings_state = 1
            self.clear_alpha_display()  # Clear display when exiting display mode
            # Reset display cache to force refresh
            self.last_num_message = None
            self.last_num_brightness = None
            self.last_alpha_message = None
            self.last_alpha_brightness = None
            self.last_alpha_type = None
            debug_lines.append(f"display_settings_callback exit: display_state={self.display_settings_state}, alarm_set={self.alarm_set}, aux_set={self.display_set}")
            print("\n".join(debug_lines), end="\n")
            return

    # --- Rotary encoder action methods ---
    def inc_alarm_hour(self):
        """
        Increment the alarm hour, wrapping around at 12.
        """
        self.alarm_hour = (self.alarm_hour % 12) + 1
        print(f"clockwise {self.alarm_hour}")
        return True

    def inc_alarm_minute(self):
        """
        Increment the alarm minute, wrapping around at 60.
        """
        self.alarm_minute = (self.alarm_minute + self.minute_incr) % 60
        print(f"clockwise {self.alarm_minute}")
        return True

    def toggle_period(self):
        """
        Toggle the alarm period between AM and PM.
        """
        self.period = "PM" if self.period == "AM" else "AM"
        print(f"clockwise {self.period}")
        return True

    def toggle_alarm_stat(self):
        """
        Toggle the alarm status between ON and OFF.
        """
        self.alarm_stat = "OFF" if self.alarm_stat == "ON" else "ON"
        print(f"clockwise {self.alarm_stat}")
        return True

    def inc_alarm_track(self):
        """
        Increment the alarm track, wrapping around at 6. Optionally play the track if audio is enabled.
        """
        self.alarm_track = (self.alarm_track % 6) + 1
        if self.use_audio:
            os.system(f"mpg123 -q {self.alarm_tracks[self.alarm_track]} &")
        return False

    def inc_vol_level(self):
        """
        Increment the volume level, wrapping around at 96. Optionally set volume if audio is enabled.
        """
        self.vol_level = (self.vol_level + 1) % 96
        if self.use_audio:
            self.mixer.setvolume(self.vol_level)
            os.system(f"mpg123 -q {self.alarm_tracks[self.alarm_track]} &")
        return False

    def dec_alarm_hour(self):
        """
        Decrement the alarm hour, wrapping around at 1.
        """
        self.alarm_hour = 12 if self.alarm_hour == 1 else self.alarm_hour - 1
        print(f"counter clockwise {self.alarm_hour}")
        return True

    def dec_alarm_minute(self):
        """
        Decrement the alarm minute, wrapping around at 0.
        """
        self.alarm_minute = (self.alarm_minute - self.minute_incr) % 60
        print(f"counter clockwise {self.alarm_minute}")
        return True

    def dec_period(self):
        """
        Toggle the alarm period between AM and PM (counterclockwise action).
        """
        self.period = "PM" if self.period == "AM" else "AM"
        print(f"counter clockwise {self.period}")
        return True

    def dec_alarm_stat(self):
        """
        Toggle the alarm status between ON and OFF (counterclockwise action).
        """
        self.alarm_stat = "OFF" if self.alarm_stat == "ON" else "ON"
        print(f"counter clockwise {self.alarm_stat}")
        return True

    def dec_alarm_track(self):
        """
        Decrement the alarm track, wrapping around at 1. Optionally play the track if audio is enabled.
        """
        self.alarm_track = 6 if self.alarm_track == 1 else self.alarm_track - 1
        if self.use_audio:
            os.system(f"mpg123 -q {self.alarm_tracks[self.alarm_track]} &")
        return False

    def dec_vol_level(self):
        """
        Decrement the volume level, wrapping around at 0. Optionally set volume if audio is enabled.
        """
        self.vol_level = 95 if self.vol_level == 0 else self.vol_level - 1
        if self.use_audio:
            self.mixer.setvolume(self.vol_level)
            os.system(f"mpg123 -q {self.alarm_tracks[self.alarm_track]} &")
        return False

    def inc_manual_dim_level(self):
        """
        Increment the manual display dim level, wrapping around at 15.
        """
        self.display_mode = "MANUAL_DIM"
        self.manual_dim_level = (self.manual_dim_level + 1) % 16
        return False

    def dec_manual_dim_level(self):
        """
        Decrement the manual display dim level, wrapping around at 0.
        """
        self.display_mode = "MANUAL_DIM"
        self.manual_dim_level = (self.manual_dim_level - 1) % 16
        return False

    def toggle_display_override(self):
        """
        Toggle the display override between ON and OFF.
        """
        self.display_override = "OFF" if self.display_override == "ON" else "ON"
        return False

    # Remove rotary_encoder_event and RotaryEncoder references
    # Add new method to handle rotary encoder polling
    def poll_rotary_encoder(self):
        """
        Poll the I2C rotary encoder for position and button events, and handle alarm/display settings accordingly.
        """
        position = self.encoder.position
        button = self.encoder_button.value
        # Detect rotation
        if position != self.last_encoder_position:
            direction = 'CLOCKWISE' if position > self.last_encoder_position else 'ANTICLOCKWISE'
            if self.alarm_settings_state == 2:
                update_time = False
                if direction == 'CLOCKWISE':
                    if self.alarm_set in self.clockwise_alarm_actions:
                        result = self.clockwise_alarm_actions[self.alarm_set]()
                        if result:
                            update_time = True
                else:
                    if self.alarm_set in self.anticlockwise_alarm_actions:
                        result = self.anticlockwise_alarm_actions[self.alarm_set]()
                        if result:
                            update_time = True
                if update_time:
                    self.alarm_time = dt.strptime(f"{self.alarm_hour}:{self.alarm_minute} {self.period}", "%I:%M %p")
            elif self.display_settings_state == 2:
                action = None
                if direction == 'CLOCKWISE':
                    action = self.clockwise_display_actions.get(self.display_set)
                else:
                    action = self.anticlockwise_display_actions.get(self.display_set)
                if action:
                    action()
                if self.alarm_ringing == 0 and (self.display_mode == "MANUAL_OFF" or self.display_mode == "AUTO_OFF"):
                    self.display_mode = "ON"
                    self.display_override = "ON"
                    self.display_settings_state = 1
                elif self.alarm_ringing == 1 and self.sleep_state == "OFF":
                    self.alarm_ringing = 0
                    self.alarm_time = self.alarm_time + datetime.timedelta(minutes=1)
                    self.sleep_state = "ON"
                elif self.alarm_ringing == 0 and self.sleep_state == "ON":
                    self.alarm_stat = "OFF"
                    self.sleep_state = "OFF"
            self.save_settings()
            self.last_encoder_position = position
        # Detect button press/release
        if not button and self.last_encoder_button:  # Button down
            self.encoder_button_down = True
        elif button and not self.last_encoder_button:  # Button up
            self.encoder_button_up = True
        # Handle button events
        if self.encoder_button_down:
            if self.alarm_settings_state == 2:
                self.alarm_set = (self.alarm_set % 6) + 1
            elif self.display_settings_state == 2:
                self.display_set = (self.display_set % 2) + 1
            self.save_settings()
            self.encoder_button_down = False
        self.last_encoder_button = button

    def poll_arcade_buttons(self):
        """
        Poll the Adafruit LED Arcade Button 1x4 for button presses and handle display/alarm settings.
        Switch 1 (yellow): Display settings, Switch 2 (white): Alarm settings.
        Also turns off a ringing or snoozed alarm when either button is pressed.
        If used to turn off a ringing/snoozed alarm, do NOT show the alphanumeric display or clear the numeric display.
        """
        now = time.monotonic()
        for idx, btn in enumerate(self.arcade_buttons):
            pressed = not btn.value # Button is active low: pressed == False
            if pressed and self.last_state[idx]:  # Button down event
                if now - self.last_press[idx] > self.debounce_time:
                    # Turn off alarm if ringing or snoozed
                    if self.alarm_ringing == 1 or self.sleep_state == "ON":
                        self.alarm_ringing = 0
                        self.alarm_stat = "OFF"
                        self.sleep_state = "OFF"
                        # Immediately clear only the alphanumeric display to stop RING, but do NOT show it or clear the numeric display
                        self.alpha_display.fill(0)
                        try:
                            self.alpha_display.show()
                        except Exception as e:
                            self.logger.error("alpha_display.show() error: %s", str(e))
                        # Do NOT clear or update the numeric display here
                        # Do NOT call display_settings_callback or alarm_settings_callback in this case
                    else:
                        if idx == 0:
                            # Switch 1 (yellow): Display settings
                            self.display_settings_callback(1)
                            self.arcade_leds[0].value = True  # Turn on yellow LED
                        elif idx == 1:
                            # Switch 2 (white): Alarm settings
                            self.alarm_settings_callback(1)
                            self.arcade_leds[1].value = True  # Turn on white LED
                    for cycle in range(0, 65535, 8000):
                        self.arcade_leds[idx].duty_cycle = cycle
                        time.sleep(0.003)
                    for cycle in range(65534, 0, -8000):
                        self.arcade_leds[idx].duty_cycle = cycle
                        time.sleep(0.003)
                self.last_press[idx] = now
            elif not pressed:
                self.arcade_leds[idx].duty_cycle = 0  # Turn off LED
            self.last_state[idx] = pressed

    def brightness(self, auto_dim, alarm_stat, display_mode, now):
        """
        Determine the display mode based on auto dim, alarm status, and current time.

        Args:
            auto_dim (str): Whether auto dim is enabled ("ON"/"OFF").
            alarm_stat (str): Alarm status ("ON"/"OFF").
            display_mode (str): Current display mode.
            now (datetime): The current datetime.
        Returns:
            str: The updated display mode.
        """
        if auto_dim == "ON":
            if dt.strptime("07:30", "%H:%M").time() <= now.time() <= dt.strptime("22:00", "%H:%M").time():
                display_mode = "MANUAL_DIM"
            elif dt.strptime("22:00", "%H:%M").time() < now.time() <= dt.strptime("23:59", "%H:%M").time():
                display_mode = "AUTO_DIM"
            if alarm_stat == "OFF":
                if dt.strptime("00:00", "%H:%M").time() < now.time() <= dt.strptime("07:00", "%H:%M").time():
                    if self.display_override == "OFF":
                        display_mode = "AUTO_OFF"
            elif alarm_stat == "ON":
                if dt.strptime("00:01", "%H:%M").time() <= now.time() < dt.strptime(self.alarm_time.time().strftime("%H:%M"), "%H:%M").time():
                    if self.display_override == "OFF":
                        display_mode = "AUTO_OFF"
                if dt.strptime(self.alarm_time.time().strftime("%H:%M"), "%H:%M").time() <= now.time() < dt.strptime("07:30", "%H:%M").time():
                    display_mode = "MANUAL_DIM"
        return display_mode

    def debug_brightness(self, auto_dim, alarm_stat, display_mode, now):
        """
        Debug version of brightness() for testing display mode logic with different time ranges.

        Args:
            auto_dim (str): Whether auto dim is enabled ("ON"/"OFF").
            alarm_stat (str): Alarm status ("ON"/"OFF").
            display_mode (str): Current display mode.
            now (datetime): The current datetime.
        Returns:
            str: The updated display mode.
        """
        if auto_dim == "ON":
            if dt.strptime("07:30", "%H:%M").time() <= now.time() <= dt.strptime("12:00", "%H:%M").time():
                display_mode = "MANUAL_DIM"
            elif dt.strptime("12:00", "%H:%M").time() < now.time() <= dt.strptime("12:59", "%H:%M").time():
                display_mode = "AUTO_DIM"
            if alarm_stat == "OFF":
                if dt.strptime("13:00", "%H:%M").time() < now.time() <= dt.strptime("15:00", "%H:%M").time():
                    if self.display_override == "OFF":
                        display_mode = "AUTO_OFF"
            elif alarm_stat == "ON":
                if dt.strptime("00:01", "%H:%M").time() <= now.time() < dt.strptime(self.alarm_time.time().strftime("%H:%M"), "%H:%M").time():
                    if self.display_override == "OFF":
                        display_mode = "AUTO_OFF"
                if dt.strptime(self.alarm_time.time().strftime("%H:%M"), "%H:%M").time() <= now.time() < dt.strptime("07:30", "%H:%M").time():
                    display_mode = "MANUAL_DIM"
        return display_mode

    def display_alpha_message(self, message_type, alpha_message, display_mode):
        """
        Display a message on the alphanumeric display, handling brightness and display mode.

        Args:
            message_type (str): Type of message ("FLOAT" or "STR").
            alpha_message: The message to display.
            display_mode (str): The current display mode.
        """
        if (display_mode == "MANUAL_OFF" or display_mode == "AUTO_OFF"):
            self.alpha_display.fill(0)
            try:
                self.alpha_display.show()
            except Exception as e:
                self.logger.error("alpha_display.show() error: %s", str(e))
            # Reset cache so next message will display
            self.last_alpha_message = None
            self.last_alpha_brightness = None
            self.last_alpha_type = None
        elif display_mode == "AUTO_DIM" or display_mode == "MANUAL_DIM":
            if display_mode == "AUTO_DIM":
                dim_level = self.auto_dim_level
            elif display_mode == "MANUAL_DIM":
                dim_level = self.manual_dim_level
            # Only update if value or brightness or type changed
            current_brightness = dim_level / 15.0
            if (alpha_message != self.last_alpha_message) or (current_brightness != self.last_alpha_brightness) or (message_type != self.last_alpha_type):
                self.alpha_display.fill(0)
                if message_type == "FLOAT":
                    self.alpha_display.print(str(alpha_message))
                elif message_type == "STR":
                    self.alpha_display.print(alpha_message)
                print(f"dim_level: {dim_level} display_mode: {display_mode}")
                self.alpha_display.brightness = current_brightness
                try:
                    self.alpha_display.show()
                except Exception as e:
                    self.logger.error("alpha_display.show() error: %s", str(e))
                self.last_alpha_message = alpha_message
                self.last_alpha_brightness = current_brightness
                self.last_alpha_type = message_type
            time.sleep(.02)
        return

    def display_num_message(self, num_message, display_mode, now):
        """
        Display a message on the numeric display, handling brightness and display mode.

        Args:
            num_message: The message to display (numeric).
            display_mode (str): The current display mode.
            now (datetime): The current datetime (for colon blink).
        """
        if (display_mode == "MANUAL_OFF" or display_mode == "AUTO_OFF"):
            self.num_display.fill(0)
            try:
                self.num_display.show()
            except Exception as e:
                self.logger.error("num_display.show() error: %s", str(e))
        elif display_mode == "AUTO_DIM" or display_mode == "MANUAL_DIM":
            if display_mode == "AUTO_DIM":
                dim_level = self.auto_dim_level
            elif display_mode == "MANUAL_DIM":
                dim_level = self.manual_dim_level
            self.num_display.fill(0)
            self.num_display.print(str(num_message))
            self.num_display.colon = now.second % 2
            self.num_display.brightness = dim_level / 15.0
            try:
                self.num_display.show()
            except Exception as e:
                self.logger.error("num_display.show() error: %s", str(e))
        time.sleep(.02)
        return

    def save_settings(self):
        """
        Save the current settings to a JSON file for persistence.
        """
        settings = {k: getattr(self, k) for k in self.PERSISTED_SETTINGS}
        # Save alarm_time as string
        settings["alarm_time"] = self.alarm_time.strftime("%H:%M")
        try:
            with open(self.SETTINGS_FILE, "w") as f:
                json.dump(settings, f)
        except Exception as e:
            self.logger.error("Failed to save settings: %s", str(e))

    def load_settings(self):
        """
        Load settings from a JSON file, updating alarm and display state variables.
        """
        try:
            with open(self.SETTINGS_FILE, "r") as f:
                settings = json.load(f)
            self.alarm_hour = settings.get("alarm_hour", self.alarm_hour)
            self.alarm_minute = settings.get("alarm_minute", self.alarm_minute)
            self.period = settings.get("period", self.period)
            self.alarm_stat = settings.get("alarm_stat", self.alarm_stat)
            self.alarm_track = settings.get("alarm_track", self.alarm_track)
            self.vol_level = settings.get("vol_level", self.vol_level)
            self.manual_dim_level = settings.get("manual_dim_level", self.manual_dim_level)
            self.auto_dim_level = settings.get("auto_dim_level", self.auto_dim_level)
            self.auto_dim = settings.get("auto_dim", self.auto_dim)
            self.display_mode = settings.get("display_mode", self.display_mode)
            self.display_override = settings.get("display_override", self.display_override)
            alarm_time_str = settings.get("alarm_time", None)
            if alarm_time_str:
                # Parse alarm_time as HH:MM (24-hour format)
                self.alarm_time = dt.strptime(alarm_time_str, "%H:%M")
                # Update alarm_hour, alarm_minute, and period to match alarm_time
                hour_24 = self.alarm_time.hour
                self.alarm_minute = self.alarm_time.minute
                if hour_24 == 0:
                    self.alarm_hour = 12
                    self.period = "AM"
                elif 1 <= hour_24 < 12:
                    self.alarm_hour = hour_24
                    self.period = "AM"
                elif hour_24 == 12:
                    self.alarm_hour = 12
                    self.period = "PM"
                else:
                    self.alarm_hour = hour_24 - 12
                    self.period = "PM"
        except FileNotFoundError:
            pass
        except Exception as e:
            self.logger.error("Failed to load settings: %s", str(e))

    def handle_gesture(self, now):
        """
        Handle gestures from the APDS9960 sensor for display wake and alarm snooze.
        Left-to-right or right-to-left gesture wakes display if off.
        Left-to-right gesture snoozes alarm if ringing.
        """
        gesture = self.apds.gesture()
        # 0x03 = left (right-to-left), 0x04 = right (left-to-right)
        if gesture in (0x03, 0x04):
            # Wake display if off
            if self.display_override == "OFF" and (self.display_mode == "AUTO_OFF" or self.display_mode == "MANUAL_OFF"):
                self.loop_count = 0
                self.display_mode = "AUTO_DIM"
                self.display_override = "ON"
                while self.loop_count <= 100:
                    now = self.get_time()
                    num_message = int(now.strftime("%I"))*100+int(now.strftime("%M"))
                    self.display_num_message(num_message, self.display_mode, now)
                    time.sleep(.03)
                    self.loop_count += 1
                # Restore previous off mode
                if self.display_mode == "AUTO_DIM":
                    self.display_mode = "AUTO_OFF"
                else:
                    self.display_mode = "MANUAL_OFF"
                self.display_override = "OFF"

    def update_main_display(self, now):
        """
        Update the main numeric display with the current time and brightness.

        Args:
            now (datetime): The current datetime.
        """
        num_message = int(now.strftime("%I"))*100+int(now.strftime("%M"))
        # Determine current brightness
        if self.display_mode == "AUTO_DIM":
            current_brightness = self.auto_dim_level / 15.0
        elif self.display_mode == "MANUAL_DIM":
            current_brightness = self.manual_dim_level / 15.0
        else:
            current_brightness = self.num_display.brightness
        # Only update if value or brightness changed
        if (num_message != self.last_num_message) or (current_brightness != self.last_num_brightness):
            self.num_display.fill(0)
            self.num_display.print(str(num_message))
            self.num_display.brightness = current_brightness
            self.last_num_message = num_message
            self.last_num_brightness = current_brightness
        # Always update colon and show, for blink effect
        self.num_display.colon = now.second % 2
        try:
            self.num_display.show()
        except Exception as e:
            self.logger.error("num_display.show() error: %s", str(e))
        self.update_alpha_display(now)

    def update_alpha_display(self, now):
        """
        Update the alphanumeric display based on the current settings and state.

        Args:
            now (datetime): The current datetime.
        """
        if self.alarm_settings_state == 2:
            if self.alarm_set == 1:
                alpha_message = self.alarm_hour*100 + self.alarm_minute
                self.display_alpha_message("FLOAT", alpha_message, self.display_mode)
            elif self.alarm_set == 2:
                alpha_message = self.alarm_hour*100 + self.alarm_minute
                self.display_alpha_message("FLOAT", alpha_message, self.display_mode)
            elif self.alarm_set == 3:
                alpha_message = self.period
                self.display_alpha_message("STR", alpha_message, self.display_mode)
            elif self.alarm_set == 4:
                alpha_message = self.alarm_stat
                self.display_alpha_message("STR", alpha_message, self.display_mode)
            elif self.alarm_set == 5:
                alpha_message = self.alarm_track
                self.display_alpha_message("FLOAT", alpha_message, self.display_mode)
                if self.use_audio:
                    os.system(f"mpg123 -q {self.alarm_tracks[self.alarm_track]} &")
            elif self.alarm_set == 6:
                alpha_message = self.vol_level
                self.display_alpha_message("FLOAT", alpha_message, self.display_mode)
                if self.use_audio:
                    self.mixer.setvolume(self.vol_level)
                    os.system(f"mpg123 -q {self.alarm_tracks[self.alarm_track]} &")
        elif self.display_settings_state == 2:
            if self.display_set == 1:
                alpha_message = self.manual_dim_level
                self.display_alpha_message("FLOAT", alpha_message, self.display_mode)
            elif self.display_set == 2:
                alpha_message = self.display_override
                self.display_alpha_message("STR", alpha_message, self.display_mode)
        elif (self.alarm_settings_state == 1 and self.display_settings_state == 1):
            self.alpha_display.fill(0)
            try:
                self.alpha_display.show()
            except Exception as e:
                self.logger.error("alpha_display.show() error: %s", str(e))

    def handle_display_off(self):
        """
        Turn off both the alphanumeric and numeric displays.
        """
        self.alpha_display.fill(0)
        try:
            self.alpha_display.show()
        except Exception as e:
            self.logger.error("alpha_display.show() error: %s", str(e))
        self.num_display.fill(0)
        try:
            self.num_display.show()
        except Exception as e:
            self.logger.error("num_display.show() error: %s", str(e))

    def main_loop_iteration(self):
        """
        Perform a single iteration of the main loop: update display, check alarm, and handle EDS wake.
        """
        now = self.get_time()
        if self.debug == "YES":
            self.display_mode = self.debug_brightness(self.auto_dim, self.alarm_stat, self.display_mode, now)
        else:
            self.display_mode = self.brightness(self.auto_dim, self.alarm_stat, self.display_mode, now)
        # Remove EDS distance check
        # self.distance = self.eds()
        # print(f"{self.distance} {self.display_mode}")
        # Remove handle_eds_wake, replace with gesture handler
        self.handle_gesture(now)
        if self.display_mode != "MANUAL_OFF":
            self.update_main_display(now)
        elif (self.display_mode == "MANUAL_OFF" or self.display_mode == "AUTO_OFF"):
            self.handle_display_off()
        if self.alarm_stat == "ON":
            self.check_alarm(now)
        self.poll_rotary_encoder()
        self.poll_arcade_buttons()

    def run(self):
        """
        Main loop for the alarm clock. Continuously updates display and checks alarm until interrupted.
        """
        try:
            while True:
                self.main_loop_iteration()
                time.sleep(0.05)
        except KeyboardInterrupt:
            self.alpha_display.fill(0)
            try:
                self.alpha_display.show()
            except Exception as e:
                self.logger.error("alpha_display.show() error: %s", str(e))
            self.num_display.fill(0)
            try:
                self.num_display.show()
            except Exception as e:
                self.logger.error("num_display.show() error: %s", str(e))
        finally:
            try:
                self.alpha_display.fill(0)
                self.alpha_display.show()
            except Exception as e:
                self.logger.error("alpha_display.show() error: %s", str(e))
            try:
                self.num_display.fill(0)
                self.num_display.show()
            except Exception as e:
                self.logger.error("num_display.show() error: %s", str(e))

if __name__ == "__main__":
    clock = AlarmClock()
    clock.run()
