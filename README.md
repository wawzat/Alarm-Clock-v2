# Alarm-Clock  
Personal project. Not fully baked. UI is not great. Code is not very well written and is unclear.  
Raspberry Pi based alarm clock with 7-segment display.  
  
Schematic  
![Alarm-Clock](./images/schematic.png)

## Features  
1. Dimmable
2. Choose alarm sound and initial volume
3. Alarm starts quietly and gradually gets louder
4. Wave to snooze and cancel alarms
5. Automatically dim and then turn off the display at preset times
5. Gesture to wake the display when it is off
 

## Operation  
The alarm clock is controlled using a rotary encoder (with push button) and two additional pushbuttons: one for Alarm Settings and one for Display Settings. Two LED displays; one shows the current time and the other shows alarm & display settings, and other status information.

### Normal Time Display
- **Default Mode:** The numeric display shows the current time in HH:MM format. The colon blinks every second.
- **Brightness:** The display brightness is manually controlled and can optionally be set to be automatically dimmed and then turned off based on time of day.

### Setting the Alarm
1. **Enter Alarm Setting Mode:**
   - Press the **Alarm Settings** button.
   - The alphanumeric display will show the alarm time or setting currently being adjusted.
2. **Adjust Alarm Hour:**
   - Rotate the encoder clockwise to increase the hour, counterclockwise to decrease.
   - Press the encoder button to move to minute adjustment.
3. **Adjust Alarm Minute:**
   - Rotate the encoder to set the minutes.
   - Press the encoder button to move to AM/PM selection.
4. **Set AM/PM:**
   - Rotate the encoder to toggle between AM and PM.
   - Press the encoder button to move to alarm ON/OFF selection.
5. **Turn Alarm ON/OFF:**
   - Rotate the encoder to toggle the alarm status.
   - Press the encoder button to finish and return to normal display.
6. - **Select Alarm Track:** Press the encoder to cycle to alarm track selection, then rotate to choose a track.
7. - **Adjust Volume:** Press again to cycle to volume adjustment, then rotate to set volume.

### Display Settings
- **Enter Display Settings:** Press the **Display Settings** button.
- **Adjust Brightness:** In Display Settings mode, rotate the encoder to change manual brightness.
- **Display Override:** Press again to select display override ON/OFF. Setting to On will cause the display to not turn off or dim automatically. 

### Alarm Operation
- **Alarm Ringing:** When the alarm time is reached and the alarm is ON, the display will show "RING" and the alarm will sound (if audio is enabled).
- **Snooze:** Wave your hand in front of the EDS sensor to snooze the alarm for 5 minute.
- **Turn Off Alarm:** Press the alarm or rotary encoder button to turn off the alarm.

### Display Modes
- **Manual/Auto Dim:** The display automatically dims or turns off at night, or you can manually adjust brightness in Display Settings mode.
- **Wake Display:** If the display is off, wave your hand in front of the EDS sensor to temporarily wake it.

### Persistent Storage
- **Automatic Saving:** Alarm and display settings (such as alarm time, brightness, alarm track, volume, and auto dim/off display) are automatically saved to persistent storage. Settings are restored after a power cycle or reboot.

### Notes
- All settings and states are displayed on the alphanumeric display.
- For more details on wiring, setup, or troubleshooting, see the rest of this README or the code comments.

## Parts List
1. 1 x Raspberry Pi Model Zero 2 W
2. 1 x SparkFun Qwiic pHAT v2.0 for Raspberry Pi - STEMMA QT / Qwiic PID: 5142
3. 1 x USB power supply for Raspberry Pi (Recommend at least 2.4 amp power supply or higher)
4. 1 x Adafruit 1.2" 4-Digit 7-Segment Display w/I2C Backpack - Yellow. Product ID: 1269
5. 1 x Adafruit Quad Alphanumeric Display - Red 0.54" Digits w/ I2C Backpack - STEMMA QT / Qwiic. Product ID: 1911
6. 1 x Adafruit I2C Stemma QT Rotary Encoder Breakout with Encoder - STEMMA QT / Qwiic PN 5880
7. 1 x Adafruit APDS9960 Proximity, Light, RGB, and Gesture Sensor - STEMMA QT / Qwiic PID: 3595
8. 1 x Adafruit I2S 3W Stereo Speaker Bonnet for Raspberry Pi - Mini Kit PID: 3346
9. 1 x Stereo Enclosed Speaker Set - 3W 4 Ohm PID: 1669
10. Stacking Header for Pi A+/B+/Pi 2/Pi 3 - 2x20 Extra Tall Header PID: 1979
11. 1 x Adafruit LED Arcade Button 1x4 - STEMMA QT I2C Breakout - STEMMA QT / Qwiic PID: 5296
12. 1 x Mini LED Arcade Button - 24mm Translucent Clear PID: 3429
13. 1 x Mini LED Arcade Button - 24mm Translucent Yellow PID: 3431
14. 4 x Arcade Button Quick-Connect Wire Pairs - 0.11" Product ID: 1152
15. 3 x 7" male x male Stemma QT cable
16. 1 x 6" male x female DuPont connector Stemma QT cable
17. 1 x 6" male x female DuPont connector Stemma QT cable modified with additional DuPont female connector.
18. 1 x 6" DuPont female x 0.1" pin (for 7-Segment 5v power)
19. 1 x USB C Jack to Micro USB Jack Round Panel Mount Adapter. Product ID: 4260
20. 1 x Micro USB to Micro USB OTG Cable - 10-12" / 25-30cm long. Product ID: 3610

## Assembly
1. Raspberry Pi / Speaker Bonnet / Qwiic pHAT Stack
- The speaker bonnet has a 2 x 20 Raspberry Pi female connector that is slim and has through holes.
- Plug the extra tall stacking header on the Raspberry Pi.
- Press the speaker bonnet as far as it will go onto stacking header pins. This leaves enough length of the pins exposed to then stack the Qwiic pHAT on top.
2. Connect the speaker plug to the speaker bonnet.
3. All of the other devices are connected to the Qwiic pHAT via Qwiic or Stemma QT cables.

## Raspberry Pi Setup
1. **SD Card Preparation**
    - Download & Open Raspberry Pi Imager  
      - Install the latest version from [raspberrypi.com](https://www.raspberrypi.com/)
    - Select Raspberry Pi OS Lite 64-bit
    - Configure Advanced Settings  
      - Set Wi-Fi SSID & Password (if using Wi-Fi)
      - Set Timezone
    - Flash SD Card  
      - Click **Write** to install OS
    - Enable SSH Manually  
      - Create an empty file named `ssh` in the boot partition
2. **Initial Setup**
    - Boot Raspberry Pi and connect it to your network
    - Connect via SSH Terminal
3. **System Configuration**
    - Run Raspberry Pi Config Tool  
      - `sudo raspi-config`
      - Enable I2C under Interfacing Options → I2C → Enable
      - Expand the filesystem
4. **Upgrade Raspberry Pi OS**
    - `sudo apt update && sudo apt upgrade -y`
5. **Install Dependencies and Utilities**
    - `sudo apt install python3-pip -y`
    - `sudo apt install screen`
    - `sudo apt install vim` (or use pre-installed nano instead)
6. **Git Setup & Repo Cloning**
    - `sudo apt install git -y`
    - `git config --global user.name "Your Name"`
    - `git config --global user.email "Your email address"`
    - `git clone https://github.com/wawzat/Alarm-Clock-v2.git`
    - `cd Alarm-Clock-v2`
    - `python -m venv .venv --system-site-packages`
    - `source .venv/bin/activate`
7. **Speaker Bonnet Configurations**
    - `wget https://github.com/adafruit/Raspberry-Pi-Installer-Scripts/raw/main/i2samp.py`
    - `sudo -E env PATH=$PATH python3 i2samp.py`  
      - Follow [Adafruit Speaker Bonnet guide](https://learn.adafruit.com/adafruit-speaker-bonnet-for-raspberry-pi)
    - `sudo vim ~/.bashrc`  
      - Add to end of file:  
        `export PYGAME_HIDE_SUPPORT_PROMPT=1`
8. **Final Step**
    - `sudo reboot`
    - `source .venv/bin/activate`
    - `python aclock.py`
