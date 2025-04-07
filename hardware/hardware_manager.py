import logging
import time
import asyncio
from threading import Thread
from typing import Optional

try:
    import RPi.GPIO as GPIO
except ImportError as e:
    raise ImportError("RPi.GPIO not found. Make sure you're running on a Raspberry Pi.") from e

from backend.audio_manager import AudioManager
from backend.settings_manager import SettingsManager

logger = logging.getLogger(__name__)

class HardwareManager:
    """Handles hardware interactions and controls for the alarm system."""
    
    # GPIO Pin Configuration
    GPIO_A = 26  # Rotary Encoder Pin A
    GPIO_B = 6   # Rotary Encoder Pin B
    BUTTON_PIN = 13  # Rotary Encoder Button
    SCHEDULE_PIN = 24  # Schedule Switch
    GLOBAL_PIN = 25  # Global Switch
    VOLUME_STEP = 5  # 5% volume adjustment step

    def __init__(self, settings_manager: SettingsManager, audio_manager: AudioManager):
        """Initialize HardwareManager with GPIO setup.
        
        Args:
            settings_manager: Manager for alarm and system settings
            audio_manager: Manager for audio playback and volume control
        """
        self.settings_manager = settings_manager
        self.audio_manager = audio_manager
        self.last_encoder_state = None  # Will be set in _setup_gpio
        
        # Initialize GPIO
        self._setup_gpio()
        logger.info("HardwareManager initialized successfully")

    def _setup_gpio(self) -> None:
        """Set up GPIO pins with proper error handling."""
        try:
            # Set GPIO mode without cleanup to avoid warnings
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)  # Suppress warnings
            
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
            
            # Bind event detection with debouncing - with proper error handling for each pin
            try:
                # First remove any existing event detection to avoid conflicts
                try:
                    GPIO.remove_event_detect(self.GPIO_A)
                except:
                    pass
                GPIO.add_event_detect(self.GPIO_A, GPIO.BOTH, 
                                    callback=self._on_rotary_rotated, 
                                    bouncetime=50)
                logger.debug(f"Added event detection for GPIO_A (pin {self.GPIO_A})")
            except Exception as e:
                logger.warning(f"Could not set up event detection for GPIO_A: {str(e)}")
                
            try:
                try:
                    GPIO.remove_event_detect(self.BUTTON_PIN)
                except:
                    pass
                GPIO.add_event_detect(self.BUTTON_PIN, GPIO.FALLING, 
                                    callback=self._on_rotary_button_pressed, 
                                    bouncetime=300)  # Increased debounce time for more reliable button press
                logger.debug(f"Added event detection for BUTTON_PIN (pin {self.BUTTON_PIN})")
            except Exception as e:
                logger.warning(f"Could not set up event detection for BUTTON_PIN: {str(e)}")
                
            try:
                try:
                    GPIO.remove_event_detect(self.SCHEDULE_PIN)
                except:
                    pass
                GPIO.add_event_detect(self.SCHEDULE_PIN, GPIO.BOTH, 
                                    callback=self._toggle_primary_schedule, 
                                    bouncetime=200)
                logger.debug(f"Added event detection for SCHEDULE_PIN (pin {self.SCHEDULE_PIN})")
            except Exception as e:
                logger.warning(f"Could not set up event detection for SCHEDULE_PIN: {str(e)}")
                
            try:
                try:
                    GPIO.remove_event_detect(self.GLOBAL_PIN)
                except:
                    pass
                GPIO.add_event_detect(self.GLOBAL_PIN, GPIO.BOTH, 
                                    callback=self._toggle_global_status, 
                                    bouncetime=200)
                logger.debug(f"Added event detection for GLOBAL_PIN (pin {self.GLOBAL_PIN})")
            except Exception as e:
                logger.warning(f"Could not set up event detection for GLOBAL_PIN: {str(e)}")
            
            logger.info("GPIO setup completed successfully")
        except Exception as e:
            logger.error(f"Failed to setup GPIO: {str(e)}")
            # Don't raise here to allow the program to continue even with partial GPIO functionality
            # Instead, we'll log the error and continue

    def _on_rotary_rotated(self, channel: int) -> None:
        """Handle rotary encoder rotation for volume control.
        
        Args:
            channel: GPIO channel that triggered the event
        """
        try:
            # Get current state of both encoder pins
            current_a = GPIO.input(self.GPIO_A)
            current_b = GPIO.input(self.GPIO_B)
            
            # Skip if no change in A pin state
            if current_a == self.last_encoder_state:
                return
                
            # Get current volume
            current_volume = self.audio_manager.get_volume()
            
            # Determine direction based on the state of both pins
            # If A and B are different, we're rotating clockwise
            # If A and B are the same, we're rotating counter-clockwise
            if current_a != current_b:
                # Clockwise rotation - increase volume
                # Calculate new volume (increase by 5)
                new_volume = min(100, current_volume + self.VOLUME_STEP)
                # Round to nearest 5
                new_volume = 5 * round(new_volume / 5)
                self.audio_manager.adjust_volume(new_volume)
                logger.info(f"Volume increased to {new_volume}%")
            # Counter-clockwise rotation - decrease volume
            else:
                # Calculate new volume (decrease by 5)
                new_volume = max(0, current_volume - self.VOLUME_STEP)
                # Round to nearest 5
                new_volume = 5 * round(new_volume / 5)
                self.audio_manager.adjust_volume(new_volume)
                logger.info(f"Volume decreased to {new_volume}%")
            
            self.last_encoder_state = current_a
            
            # Broadcast volume update via WebSocket
            self._broadcast_volume_update(new_volume)
            
        except Exception as e:
            logger.error(f"Error in rotary encoder handling: {str(e)}")

    def _broadcast_volume_update(self, volume: int) -> None:
        """Broadcast volume update via WebSocket."""
        try:
            # Import here to avoid circular imports
            from backend.websocket_manager import connection_manager
            
            # Run the broadcast in a background task to avoid blocking
            asyncio.create_task(connection_manager.broadcast_volume_update(volume))
        except Exception as e:
            logger.error(f"Failed to broadcast volume update: {e}")

    def _on_rotary_button_pressed(self, channel: int) -> None:
        """Toggle white noise playback.
        
        Args:
            channel: GPIO channel that triggered the event
        """
        try:
            # Check if white noise is currently playing
            was_playing = self.audio_manager.is_white_noise_playing()
            
            # Toggle white noise
            result = self.audio_manager.toggle_white_noise()
            
            # Log the action with clear status
            if was_playing:
                logger.info("White noise turned OFF by rotary button press")
            else:
                logger.info("White noise turned ON by rotary button press")
            
            # Note: We don't need to broadcast here since audio_manager.toggle_white_noise already broadcasts
                
            return result
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
            
            # Log with more descriptive message
            schedule_name = "Primary" if state else "Secondary"
            logger.info(f"Schedule switched to: {schedule_name} (value={state})")
            
            # Broadcast schedule update via WebSocket
            self._broadcast_schedule_update(state)
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
            
            # Log with more descriptive message
            status_text = "ON" if state else "OFF"
            logger.info(f"Global alarm system turned {status_text} (value={state})")
            
            # Broadcast global status update via WebSocket
            self._broadcast_global_status_update(state)
        except Exception as e:
            logger.error(f"Error toggling global status: {str(e)}")

    def cleanup(self) -> None:
        """Clean up GPIO resources."""
        try:
            GPIO.cleanup()
            logger.info("GPIO resources cleaned up successfully")
            
            # Broadcast system shutdown via WebSocket
            self._broadcast_shutdown()
        except Exception as e:
            logger.error(f"Error during GPIO cleanup: {str(e)}")
            raise
            
    def _broadcast_schedule_update(self, is_primary: bool) -> None:
        """Broadcast schedule update via WebSocket."""
        try:
            # Import here to avoid circular imports
            from backend.websocket_manager import connection_manager
            
            # Run the broadcast in a background task to avoid blocking
            asyncio.create_task(connection_manager.broadcast_schedule_update(is_primary))
        except Exception as e:
            logger.error(f"Failed to broadcast schedule update: {e}")
    
    def _broadcast_global_status_update(self, is_on: bool) -> None:
        """Broadcast global status update via WebSocket."""
        try:
            # Import here to avoid circular imports
            from backend.websocket_manager import connection_manager
            
            # Run the broadcast in a background task to avoid blocking
            asyncio.create_task(connection_manager.broadcast_global_status_update(is_on))
        except Exception as e:
            logger.error(f"Failed to broadcast global status update: {e}")
    
    def _broadcast_shutdown(self) -> None:
        """Broadcast system shutdown via WebSocket."""
        try:
            # Import here to avoid circular imports
            from backend.websocket_manager import connection_manager
            
            # Run the broadcast in a background task to avoid blocking
            asyncio.create_task(connection_manager.broadcast_shutdown())
        except Exception as e:
            logger.error(f"Failed to broadcast shutdown: {e}")

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
