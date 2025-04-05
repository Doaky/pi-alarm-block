import logging
import time
from threading import Thread
from typing import Optional

try:
    import RPi.GPIO as GPIO
except ImportError as e:
    raise ImportError("RPi.GPIO not found. Make sure you're running on a Raspberry Pi.") from e

from backend.audio_manager import AudioManager
from backend.settings_manager import SettingsManager

logger = logging.getLogger(__name__)

class PiHandler:
    """Handles Raspberry Pi GPIO interactions and hardware controls."""
    
    # GPIO Pin Configuration
    GPIO_A = 26  # Rotary Encoder Pin A
    GPIO_B = 6   # Rotary Encoder Pin B
    BUTTON_PIN = 13  # Rotary Encoder Button
    SCHEDULE_PIN = 24  # Schedule Switch
    GLOBAL_PIN = 25  # Global Switch
    VOLUME_STEP = 0.05  # 5% volume adjustment step

    def __init__(self, settings_manager: SettingsManager, audio_manager: AudioManager):
        """Initialize PiHandler with GPIO setup.
        
        Args:
            settings_manager: Manager for alarm and system settings
            audio_manager: Manager for audio playback and volume control
        """
        self.settings_manager = settings_manager
        self.audio_manager = audio_manager
        self.last_encoder_state = None  # Will be set in _setup_gpio
        
        # Initialize GPIO
        self._setup_gpio()
        logger.info("PiHandler initialized successfully")

    def _setup_gpio(self) -> None:
        """Set up GPIO pins with proper error handling."""
        try:
            GPIO.cleanup()
            GPIO.setmode(GPIO.BCM)
            
            # Setup input pins with pull-up resistors
            pins = [
                self.GPIO_A,
                self.GPIO_B,
                self.BUTTON_PIN,
                self.SCHEDULE_PIN,
                self.GLOBAL_PIN
            ]
            
            for pin in pins:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Initialize encoder state
            self.last_encoder_state = GPIO.input(self.GPIO_A)
            
            # Bind event detection with debouncing
            GPIO.add_event_detect(self.GPIO_A, GPIO.BOTH, 
                                callback=self._on_rotary_rotated, 
                                bouncetime=50)
            GPIO.add_event_detect(self.BUTTON_PIN, GPIO.FALLING, 
                                callback=self._on_rotary_button_pressed, 
                                bouncetime=200)
            GPIO.add_event_detect(self.SCHEDULE_PIN, GPIO.BOTH, 
                                callback=self._toggle_primary_schedule, 
                                bouncetime=200)
            GPIO.add_event_detect(self.GLOBAL_PIN, GPIO.BOTH, 
                                callback=self._toggle_global_status, 
                                bouncetime=200)
            
            logger.info("GPIO setup completed successfully")
        except Exception as e:
            logger.error(f"Failed to setup GPIO: {str(e)}")
            raise

    def _on_rotary_rotated(self, channel: int) -> None:
        """Handle rotary encoder rotation for volume control.
        
        Args:
            channel: GPIO channel that triggered the event
        """
        try:
            current_a = GPIO.input(self.GPIO_A)
            current_b = GPIO.input(self.GPIO_B)
            
            if current_a != self.last_encoder_state:
                # Get current volume
                current_volume = self.audio_manager.get_volume()
                
                # Clockwise rotation - increase volume
                if current_b != current_a:
                    # Calculate new volume (increase by 5%)
                    new_volume = min(100, current_volume + int(self.VOLUME_STEP * 100))
                    self.audio_manager.adjust_volume(new_volume)
                    logger.info(f"Volume increased to {new_volume}%")
                # Counter-clockwise rotation - decrease volume
                else:
                    # Calculate new volume (decrease by 5%)
                    new_volume = max(0, current_volume - int(self.VOLUME_STEP * 100))
                    self.audio_manager.adjust_volume(new_volume)
                    logger.info(f"Volume decreased to {new_volume}%")
            
            self.last_encoder_state = current_a
            
        except Exception as e:
            logger.error(f"Error in rotary encoder handling: {str(e)}")

    def _on_rotary_button_pressed(self, channel: int) -> None:
        """Toggle white noise playback.
        
        Args:
            channel: GPIO channel that triggered the event
        """
        try:
            self.audio_manager.toggle_white_noise()
        except Exception as e:
            logger.error(f"Error handling rotary button press: {str(e)}")

    def _toggle_primary_schedule(self, channel: int) -> None:
        """Update schedule setting based on switch state.
        
        Args:
            channel: GPIO channel that triggered the event
        """
        try:
            state = GPIO.input(self.SCHEDULE_PIN)
            self.settings_manager.set_is_primary_schedule(state)
            logger.info(f"Primary schedule toggled to: {state}")
        except Exception as e:
            logger.error(f"Error toggling schedule: {str(e)}")

    def _toggle_global_status(self, channel: int) -> None:
        """Update global alarm status based on switch state.
        
        Args:
            channel: GPIO channel that triggered the event
        """
        try:
            state = GPIO.input(self.GLOBAL_PIN)
            self.settings_manager.set_is_global_on(state)
            logger.info(f"Global status toggled to: {state}")
        except Exception as e:
            logger.error(f"Error toggling global status: {str(e)}")

    def cleanup(self) -> None:
        """Clean up GPIO resources."""
        try:
            GPIO.cleanup()
            logger.info("GPIO resources cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during GPIO cleanup: {str(e)}")
            raise

    def __del__(self) -> None:
        """Ensure cleanup on object destruction."""
        self.cleanup()

    def start_system(self) -> None:
        """Start the system and wait for events."""
        logger.info("Starting GPIO event handling system...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("GPIO system shutting down...")
            self.cleanup()

    def run(self) -> None:
        """Run the GPIO system in a separate thread."""
        system_thread = Thread(target=self.start_system, daemon=True)
        system_thread.start()
        logger.info("GPIO system thread started")
