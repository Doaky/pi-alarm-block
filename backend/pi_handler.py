# import logging
# import os
# import random
# import time
# from threading import Thread, Lock
# from typing import Optional

# try:
#     import RPi.GPIO as GPIO
#     import pygame
# except ImportError as e:
#     raise ImportError("Required hardware libraries not found. Make sure you're running on a Raspberry Pi with RPi.GPIO and pygame installed.") from e

# # Configure logging
# logger = logging.getLogger(__name__)

# class PiHandler:
#     """Handles Raspberry Pi GPIO and audio interactions."""
    
#     # GPIO Pin Configuration
#     GPIO_A = 26  # Rotary Encoder Pin A
#     GPIO_B = 6   # Rotary Encoder Pin B
#     BUTTON_PIN = 13  # Rotary Encoder Button
#     SCHEDULE_PIN = 24  # Schedule Switch
#     GLOBAL_PIN = 25  # Global Switch
#     VOLUME_STEP = 0.05  # 5% volume adjustment step

#     def __init__(self, settings_manager, sounds_dir: str = "backend/sounds/", white_noise_file: str = "white_noise.mp3"):
#         """Initialize PiHandler with GPIO setup and audio configuration."""
#         self.settings_manager = settings_manager
#         self.sounds_dir = sounds_dir
#         self.white_noise_file = os.path.join(sounds_dir, white_noise_file)
        
#         # Audio state
#         self.alarm_volume = 0.5  # 50% initial alarm volume
#         self.white_noise_volume = 0.1  # 10% initial white noise volume
#         self.white_noise_playing = False
#         self._volume_lock = Lock()  # Thread-safe volume control
#         self.last_encoder_state = GPIO.input(self.GPIO_A)  # Initialize last encoder state

#         # Initialize GPIO
#         self._setup_gpio()
        
#         # Initialize audio
#         self._setup_audio()
        
#         logger.info("PiHandler initialized successfully")

#     def _setup_gpio(self):
#         """Set up GPIO pins with proper error handling."""
#         try:
#             GPIO.cleanup()
#             GPIO.setmode(GPIO.BCM)
            
#             # Setup input pins with pull-up resistors
#             pins = [
#                 self.GPIO_A,
#                 self.GPIO_B,
#                 self.BUTTON_PIN,
#                 self.SCHEDULE_PIN,
#                 self.GLOBAL_PIN
#             ]
            
#             for pin in pins:
#                 GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
#             # Bind event detection with debouncing
#             GPIO.add_event_detect(self.GPIO_A, GPIO.BOTH, 
#                                 callback=self._on_rotary_rotated, 
#                                 bouncetime=50)
#             GPIO.add_event_detect(self.BUTTON_PIN, GPIO.FALLING, 
#                                 callback=self._on_rotary_button_pressed, 
#                                 bouncetime=200)
#             GPIO.add_event_detect(self.SCHEDULE_PIN, GPIO.BOTH, 
#                                 callback=self._toggle_primary_schedule, 
#                                 bouncetime=200)
#             GPIO.add_event_detect(self.GLOBAL_PIN, GPIO.BOTH, 
#                                 callback=self._toggle_global_status, 
#                                 bouncetime=200)
            
#             logger.info("GPIO setup completed successfully")
#         except Exception as e:
#             logger.error(f"Failed to setup GPIO: {str(e)}")
#             raise

#     def _setup_audio(self):
#         """Initialize pygame audio mixer with error handling."""
#         try:
#             pygame.mixer.init()
#             logger.info("Audio system initialized successfully")
#         except Exception as e:
#             logger.error(f"Failed to initialize audio system: {str(e)}")
#             raise

#     def _on_rotary_rotated(self, channel):
#         """Handle rotary encoder rotation for volume control with thread safety."""
#         try:
#             with self._volume_lock:
#                 current_a = GPIO.input(self.GPIO_A)
#                 current_b = GPIO.input(self.GPIO_B)
                
#                 if current_a != self.last_encoder_state:
#                     if current_b != current_a:
#                         self.white_noise_volume = min(1.0, self.white_noise_volume + self.VOLUME_STEP)
#                         logger.debug(f"Volume increased to {self.white_noise_volume:.2f}")
#                     else:
#                         self.white_noise_volume = max(0.0, self.white_noise_volume - self.VOLUME_STEP)
#                         logger.debug(f"Volume decreased to {self.white_noise_volume:.2f}")
                    
#                     if self.white_noise_playing:
#                         pygame.mixer.music.set_volume(self.white_noise_volume)
                
#                 self.last_encoder_state = current_a
#         except Exception as e:
#             logger.error(f"Error in rotary encoder handling: {str(e)}")

#     def _on_rotary_button_pressed(self, channel):
#         """Toggle white noise playback with debouncing."""
#         try:
#             if self.white_noise_playing:
#                 self.stop_white_noise()
#             else:
#                 self.play_white_noise()
#         except Exception as e:
#             logger.error(f"Error handling rotary button press: {str(e)}")

#     def _toggle_primary_schedule(self, channel):
#         """Update schedule setting based on switch state."""
#         try:
#             state = GPIO.input(self.SCHEDULE_PIN)
#             self.settings_manager.set_is_primary_schedule(state)
#             logger.info(f"Primary schedule toggled to: {state}")
#         except Exception as e:
#             logger.error(f"Error toggling schedule: {str(e)}")

#     def _toggle_global_status(self, channel):
#         """Update global alarm status based on switch state."""
#         try:
#             state = GPIO.input(self.GLOBAL_PIN)
#             self.settings_manager.set_is_global_on(state)
#             logger.info(f"Global status toggled to: {state}")
#         except Exception as e:
#             logger.error(f"Error toggling global status: {str(e)}")

#     def play_white_noise(self):
#         """Start white noise playback with error handling."""
#         try:
#             pygame.mixer.music.load(self.white_noise_file)
#             pygame.mixer.music.set_volume(self.white_noise_volume)
#             pygame.mixer.music.play(loops=-1)
#             self.white_noise_playing = True
#             logger.info("White noise playback started")
#         except Exception as e:
#             logger.error(f"Failed to start white noise playback: {str(e)}")
#             self.white_noise_playing = False
#             raise

#     def stop_white_noise(self):
#         """Stop white noise playback with error handling."""
#         try:
#             pygame.mixer.music.stop()
#             self.white_noise_playing = False
#             logger.info("White noise playback stopped")
#         except Exception as e:
#             logger.error(f"Failed to stop white noise playback: {str(e)}")
#             raise

#     def play_alarm(self):
#         """Play alarm sound with gradual volume increase."""
#         try:
#             alarm_files = [f for f in os.listdir(os.path.join(self.sounds_dir, "alarm_sounds")) 
#                           if f.endswith('.mp3')]
#             if not alarm_files:
#                 raise FileNotFoundError("No alarm sound files found")
            
#             alarm_file = random.choice(alarm_files)
#             alarm_path = os.path.join(self.sounds_dir, "alarm_sounds", alarm_file)
            
#             alarm_sound = pygame.mixer.Sound(alarm_path)
#             alarm_sound.set_volume(self.alarm_volume)
#             alarm_sound.play()
            
#             # Start volume fade-in thread
#             Thread(target=self._fade_in_alarm, daemon=True).start()
#             logger.info(f"Playing alarm sound: {alarm_file}")
#         except Exception as e:
#             logger.error(f"Failed to play alarm: {str(e)}")
#             raise

#     def _fade_in_alarm(self):
#         """Gradually increase alarm volume."""
#         try:
#             start_time = time.time()
#             while self.alarm_volume < 0.5:  # Target: 50% volume
#                 elapsed_time = time.time() - start_time
#                 if elapsed_time < 60:  # Fade in over 60 seconds
#                     with self._volume_lock:
#                         self.alarm_volume = min(0.5, (elapsed_time / 60) * 0.5)
#                         pygame.mixer.music.set_volume(self.alarm_volume)
#                     time.sleep(1)
#                 else:
#                     break
#         except Exception as e:
#             logger.error(f"Error during alarm fade-in: {str(e)}")

#     def stop_alarm(self):
#         """Stop alarm playback with error handling."""
#         try:
#             pygame.mixer.music.stop()
#             logger.info("Alarm stopped")
#         except Exception as e:
#             logger.error(f"Failed to stop alarm: {str(e)}")
#             raise

#     def cleanup(self):
#         """Clean up GPIO and audio resources."""
#         try:
#             pygame.mixer.quit()
#             GPIO.cleanup()
#             logger.info("Resources cleaned up successfully")
#         except Exception as e:
#             logger.error(f"Error during cleanup: {str(e)}")
#             raise

#     def __del__(self):
#         """Ensure cleanup on object destruction."""
#         self.cleanup()

#     def start_system(self):
#         """Start the system and wait for events."""
#         print("Starting system...")
#         try:
#             while True:
#                 time.sleep(1)
#         except KeyboardInterrupt:
#             print("Exiting...")
#             self.cleanup()

#     def run(self):
#         """Run the system in a separate thread."""
#         system_thread = Thread(target=self.start_system)
#         system_thread.start()
        
#         # Simulate an alarm being triggered for demonstration purposes
#         self.play_alarm()
#         self.increase_alarm_volume()

#     def increase_alarm_volume(self):
#         """Gradually increase the alarm volume to 50%."""
#         start_time = time.time()
#         target_volume = 0.5  # Target alarm volume
#         while self.alarm_volume < target_volume:
#             elapsed_time = time.time() - start_time
#             if elapsed_time < 60:
#                 self.alarm_volume = min(target_volume, (elapsed_time / 60) * target_volume)
#                 pygame.mixer.music.set_volume(self.alarm_volume)
#                 time.sleep(1)
#             else:
#                 break
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
