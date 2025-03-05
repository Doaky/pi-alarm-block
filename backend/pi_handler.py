#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import pygame

# GPIO Pins for Encoder and Buttons
GPIO_A = 26  # GPIO pin for encoder A
GPIO_B = 6   # GPIO pin for encoder B
BUTTON_PIN = 13  # GPIO pin for mute button
PLAY_PAUSE_PIN = 5  # GPIO pin for play/pause button

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PLAY_PAUSE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize Pygame Mixer
pygame.mixer.init()
pygame.mixer.music.load("test.mp3")  # Load a sample MP3 file
pygame.mixer.music.play(-1)  # Loop the music

# Variables to track rotary encoder state and playback status
last_state = GPIO.input(GPIO_A)
counter = 50  # Start at 50% volume
muted = False  # Initial mute state
paused = False  # Initial play state

# Function to control volume using pygame
def set_volume(level):
    """ Set the volume level using Pygame, ensuring it's between 0 and 100 """
    level = max(0, min(level, 100))  # Ensure volume is within range
    pygame.mixer.music.set_volume(level / 100.0)  # Convert 0-100 to 0.0-1.0
    print(f"Volume: {level}%")

# Function to mute/unmute
def toggle_mute():
    """ Toggle mute state """
    global muted, counter
    if muted:
        pygame.mixer.music.set_volume(counter / 100.0)
        print("Unmuted")
    else:
        pygame.mixer.music.set_volume(0.0)
        print("Muted")
    muted = not muted

# Function to play/pause
def toggle_play_pause():
    """ Toggle play/pause state """
    global paused
    if paused:
        pygame.mixer.music.unpause()
        print("Resumed")
    else:
        pygame.mixer.music.pause()
        print("Paused")
    paused = not paused

# Function to handle rotary encoder changes
def update_encoder(channel):
    global last_state, counter
    current_state = GPIO.input(GPIO_A)

    if last_state == GPIO.LOW and current_state == GPIO.HIGH:
        if GPIO.input(GPIO_B) == GPIO.LOW:
            counter -= 5  # Decrease volume
        else:
            counter += 5  # Increase volume

        counter = max(0, min(counter, 100))  # Constrain volume
        set_volume(counter)

    last_state = current_state

# Function to handle mute button press
def button_pressed(channel):
    toggle_mute()

# Function to handle play/pause button press
def play_pause_pressed(channel):
    toggle_play_pause()

# Set up interrupts for rotary encoder and buttons
GPIO.add_event_detect(GPIO_A, GPIO.BOTH, callback=update_encoder)
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=button_pressed, bouncetime=300)
GPIO.add_event_detect(PLAY_PAUSE_PIN, GPIO.FALLING, callback=play_pause_pressed, bouncetime=300)

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