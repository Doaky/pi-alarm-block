import os
import random
import time
import pygame
import RPi.GPIO as GPIO
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

        # GPIO Setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Rotary Encoder A
        GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP)   # Rotary Encoder B
        GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Encoder Button
        GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Schedule Switch
        GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Global Switch

        # Rotary Encoder state
        self.last_encoder_state = GPIO.input(26)
        
        # Bind event detection
        GPIO.add_event_detect(26, GPIO.BOTH, callback=self._on_rotary_rotated, bouncetime=50)
        GPIO.add_event_detect(13, GPIO.FALLING, callback=self._on_rotary_button_pressed, bouncetime=200)
        GPIO.add_event_detect(24, GPIO.BOTH, callback=self._toggle_primary_schedule, bouncetime=200)
        GPIO.add_event_detect(25, GPIO.BOTH, callback=self._toggle_global_status, bouncetime=200)
    
    def _on_rotary_rotated(self, channel):
        """Handle the rotary encoder rotation to adjust the volume."""
        current_state = GPIO.input(26)
        if current_state != self.last_encoder_state:  # Ensure state change
            if GPIO.input(6) != current_state:
                direction = "clockwise"
                if self.white_noise_volume < 1.0:
                    self.white_noise_volume += 0.05
            else:
                direction = "counterclockwise"
                if self.white_noise_volume > 0.05:
                    self.white_noise_volume -= 0.05
            self.last_encoder_state = current_state
            print(f"Encoder Rotated {direction}")
        
        if self.white_noise_playing:
            pygame.mixer.music.set_volume(self.white_noise_volume)
    
    def _on_rotary_button_pressed(self, channel):
        """Toggle the playback of white noise when the rotary encoder button is pressed."""
        print("Encoder Pressed")
        if self.white_noise_playing:
            self.stop_white_noise()
        else:
            self.play_white_noise()
    
    def _toggle_primary_schedule(self, channel):
        """Toggle the primary schedule setting based on switch state."""
        state = GPIO.input(24)
        self.settings_manager.set_is_primary_schedule(state)
        print(f"Primary schedule set to {state}")
    
    def _toggle_global_status(self, channel):
        """Toggle the global status setting based on switch state."""
        state = GPIO.input(25)
        self.settings_manager.set_is_global_on(state)
        print(f"Global status set to {state}")
    
    def play_white_noise(self):
        """Play the white noise sound file in a loop."""
        print("White noise playing")
        self.white_noise_playing = True
        pygame.mixer.music.load(self.white_noise_file)
        pygame.mixer.music.set_volume(self.white_noise_volume)
        pygame.mixer.music.play(loops=-1)
    
    def stop_white_noise(self):
        """Stop the white noise playback."""
        print("White noise stop")
        self.white_noise_playing = False
        pygame.mixer.music.stop()
    
    def play_alarm(self):
        """Play a random alarm sound."""
        alarm_file = random.choice([f for f in os.listdir(self.sounds_dir) if f.endswith('.mp3')])
        alarm_path = os.path.join(self.sounds_dir, alarm_file)
        alarm_sound = pygame.mixer.Sound(alarm_path)
        alarm_sound.set_volume(self.alarm_volume)
        alarm_sound.play()
    
    def increase_alarm_volume(self):
        """Gradually increase the alarm volume to 50%."""
        start_time = time.time()
        target_volume = 0.5  # Target alarm volume
        while self.alarm_volume < target_volume:
            elapsed_time = time.time() - start_time
            if elapsed_time < 60:
                self.alarm_volume = min(target_volume, (elapsed_time / 60) * target_volume)
                pygame.mixer.music.set_volume(self.alarm_volume)
                time.sleep(1)
            else:
                break
    
    def cleanup(self):
        """Clean up GPIO on exit."""
        GPIO.cleanup()
    
    def start_system(self):
        """Start the system and wait for events."""
        print("Starting system...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Exiting...")
            self.cleanup()
    
    def run(self):
        """Run the system in a separate thread."""
        system_thread = Thread(target=self.start_system)
        system_thread.start()
        
        # Simulate an alarm being triggered for demonstration purposes
        self.play_alarm()
        self.increase_alarm_volume()
