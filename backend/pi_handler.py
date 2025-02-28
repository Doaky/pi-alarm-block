import os
import random
import time
from time import sleep
import pygame
from gpiozero import RotaryEncoder, Button, Switch
from threading import Thread

class PiHandler:
    def __init__(self, settings_manager, sounds_dir="sounds", white_noise_file="white_noise.mp3"):
        # Initialize pygame mixer for sound playback
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        # Initialize the SettingsManager to change global and schedule settings
        self.settings_manager = settings_manager

        # Setup initial variables
        self.sounds_dir = sounds_dir
        self.white_noise_file = os.path.join(sounds_dir, white_noise_file)
        self.alarm_volume = 0.5  # 50% initial alarm volume
        self.white_noise_volume = 0.1  # 10% initial white noise volume
        self.white_noise_playing = False

        # Setup GPIO for Rotary Encoder and Button (for volume control and white noise toggle)
        self.rotary_encoder = RotaryEncoder(17, 18)  # GPIO pins for rotary encoder
        self.encoder_button = Button(23)  # GPIO pin for rotary encoder button

        # Setup GPIO switches for toggling schedule and global on/off
        self.schedule_switch = Switch(24)  # GPIO pin for schedule switch (toggles is_primary_schedule)
        self.global_switch = Switch(25)  # GPIO pin for global status switch (toggles is_global_on)

        # Bind events for rotary encoder, button, and switches
        self._setup_rotary_encoder()
        self._setup_switches()

    def _setup_rotary_encoder(self):
        """Setup rotary encoder to adjust volume and toggle white noise playback."""
        self.rotary_encoder.when_rotated = self._on_rotary_rotated
        self.rotary_encoder.when_button_pressed = self._on_rotary_button_pressed

    def _setup_switches(self):
        """Setup switches for toggling global status and primary schedule."""
        self.schedule_switch.when_pressed = self._toggle_primary_schedule
        self.global_switch.when_pressed = self._toggle_global_status

    def _on_rotary_rotated(self):
        """Handle the rotary encoder rotation to adjust the volume."""
        if self.rotary_encoder.direction == 'clockwise' and self.white_noise_volume < 1.0:
            self.white_noise_volume += 0.05  # Increase volume by 5%
        elif self.rotary_encoder.direction == 'counterclockwise' and self.white_noise_volume > 0.05:
            self.white_noise_volume -= 0.05  # Decrease volume by 5%, but not below 5%

        # Update the white noise volume if it's playing
        if self.white_noise_playing:
            pygame.mixer.music.set_volume(self.white_noise_volume)

    def _on_rotary_button_pressed(self):
        """Toggle the playback of white noise when the rotary encoder button is pressed."""
        if self.white_noise_playing:
            self.stop_white_noise()
        else:
            self.play_white_noise()

    def _toggle_primary_schedule(self):
        """Toggle the primary schedule setting based on switch state."""
        if self.schedule_switch.value:  # True when the switch is flipped up
            self.settings_manager.set_is_primary_schedule(True)
            print("Primary schedule set to True")
        else:  # False when the switch is flipped down
            self.settings_manager.set_is_primary_schedule(False)
            print("Primary schedule set to False")

    def _toggle_global_status(self):
        """Toggle the global status setting based on switch state."""
        if self.global_switch.value:  # True when the switch is flipped up
            self.settings_manager.set_is_global_on(True)
            print("Global status set to True")
        else:  # False when the switch is flipped down
            self.settings_manager.set_is_global_on(False)
            print("Global status set to False")

    def play_white_noise(self):
        """Play the white noise sound file in a loop."""
        self.white_noise_playing = True
        pygame.mixer.music.load(self.white_noise_file)
        pygame.mixer.music.set_volume(self.white_noise_volume)
        pygame.mixer.music.play(loops=-1)  # Play indefinitely

    def stop_white_noise(self):
        """Stop the white noise playback."""
        self.white_noise_playing = False
        pygame.mixer.music.stop()

    def play_alarm(self):
        """Play a random alarm sound."""
        alarm_file = random.choice([f for f in os.listdir(self.sounds_dir) if f.endswith('.mp3')])
        alarm_path = os.path.join(self.sounds_dir, alarm_file)
        alarm_sound = pygame.mixer.Sound(alarm_path)
        alarm_sound.set_volume(self.alarm_volume)
        alarm_sound.play()

    def pause_alarm(self):
        """Pause the alarm sound when needed."""
        pygame.mixer.music.stop()

    def increase_alarm_volume(self):
        """Gradually increase the alarm volume to 50%."""
        start_time = time.time()
        target_volume = 0.5  # Target alarm volume (50%)
        while self.alarm_volume < target_volume:
            elapsed_time = time.time() - start_time
            if elapsed_time < 60:  # Gradually increase volume over 60 seconds
                self.alarm_volume = min(target_volume, (elapsed_time / 60) * target_volume)
                pygame.mixer.music.set_volume(self.alarm_volume)
                sleep(1)
            else:
                break

    def start_system(self):
        """Start the system and wait for events."""
        print("Starting system...")
        while True:
            # Wait for the alarm to be triggered or other system events
            pass

    def run(self):
        """Run the system in a separate thread."""
        system_thread = Thread(target=self.start_system)
        system_thread.start()

        # Simulate an alarm being triggered for demonstration purposes
        self.play_alarm()
        self.increase_alarm_volume()  # Gradually increase alarm volume
