import time
import RPi.GPIO as GPIO
from subprocess import run

BUTTON_PIN = 10  # GPIO pin for button
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def play_alarm():
    run(["aplay", "/home/pi/alarm.wav"])  # Plays alarm sound

def stop_alarm():
    run(["pkill", "aplay"])  # Stops audio playback

def listen_for_button():
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            stop_alarm()
        time.sleep(0.1)

# Run button listener in the background
import threading
button_thread = threading.Thread(target=listen_for_button, daemon=True)
button_thread.start()
