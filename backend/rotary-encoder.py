#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import subprocess

# GPIO Pins for Encoder and Button
GPIO_A = 26  # GPIO pin for encoder A
GPIO_B = 6   # GPIO pin for encoder B
BUTTON_PIN = 13  # GPIO pin for button

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Variables to track rotary encoder state and mute status
last_state = GPIO.input(GPIO_A)
counter = 50  # Start at 50% volume
muted = False  # Initial mute state

# Function to control volume using PulseAudio (pactl)
def set_volume(level):
    """ Set the volume level using PulseAudio, ensuring it's between 0 and 100 """
    level = max(0, min(level, 160))  # Ensure volume is between 0 and 100
    # Use pactl to set the volume of the PulseAudio sink
    subprocess.run(['pactl', 'set-sink-volume', 'alsa_output.platform-soc_sound.stereo-fallback', f'{level}%'])

# Function to mute/unmute using PulseAudio (pactl)
def toggle_mute():
    """ Toggle mute state using PulseAudio """
    global muted
    if muted:
        subprocess.run(['pactl', 'set-sink-mute', 'alsa_output.platform-soc_sound.stereo-fallback', '0'])  # Unmute
        print("Unmuted")
    else:
        subprocess.run(['pactl', 'set-sink-mute', 'alsa_output.platform-soc_sound.stereo-fallback', '1'])  # Mute
        print("Muted")
    muted = not muted

# Function to handle rotary encoder changes
def update_encoder(channel):
    global last_state, counter
    current_state = GPIO.input(GPIO_A)

    # Check if rotary encoder has moved
    if last_state == GPIO.LOW and current_state == GPIO.HIGH:
        if GPIO.input(GPIO_B) == GPIO.LOW:
            counter -= 5  # Rotate clockwise (decrease volume)
        else:
	    counter += 5  # Rotate counter-clockwise (increase volume)

        # Constrain volume between 0 and 100
        counter = max(0, min(counter, 160))

        # Set volume level and print the counter
        set_volume(counter)
        print(f"Volume: {counter}%")

    last_state = current_state

# Function to handle button press (mute toggle)
def button_pressed(channel):
    toggle_mute()

# Set up interrupt for rotary encoder
GPIO.add_event_detect(GPIO_A, GPIO.BOTH, callback=update_encoder)
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=button_pressed, bouncetime=300)

# Set the initial volume
set_volume(counter)

# Keep the program running
try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Program exiting...")

finally:
    GPIO.cleanup()
