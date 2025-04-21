import asyncio
import logging
import time
from threading import Thread

import RPi.GPIO as GPIO

from backend.services.audio_manager import AudioManager
from backend.services.settings_manager import SettingsManager
from backend.services.websocket_manager import WebSocketManager
from backend.config import DEV_MODE

logger = logging.getLogger(__name__)

class HardwareManager:
    """Handles hardware interactions and controls for the alarm block."""
    
    # GPIO Pin Constants
    ROTARY_PIN_A = 26  # Rotary Encoder Pin A
    ROTARY_PIN_B = 6  # Rotary Encoder Pin B
    ROTARY_BUTTON_PIN = 13  # Rotary Encoder Button

    PRIMARY_SCHEDULE_PIN = 24  # Primary Schedule Switch Pin
    SECONDARY_SCHEDULE_PIN = 25  # Secondary Schedule Switch Pin
    GLOBAL_PIN = 27  # Global Switch
   

    # Constants
    VOLUME_STEP = 5  # 5% volume adjustment step
    
    def __init__(self, settings_manager: SettingsManager, audio_manager: AudioManager):
        """Initialize HardwareManager with GPIO setup.
        
        Args:
            settings_manager: Manager for alarm block settings
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
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(DEV_MODE)
            
            # Set up GPIO
            # White Noise Rotary encoder
            GPIO.setup(self.ROTARY_PIN_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.ROTARY_PIN_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.ROTARY_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Schedule Switch
            GPIO.setup(self.PRIMARY_SCHEDULE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.SECONDARY_SCHEDULE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.GLOBAL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Alarm button
            # TODO add alarm off button pin

            # Power button
            # TODO add power button pin
            
            # Initialize encoder state
            self.last_encoder_state = GPIO.input(self.ROTARY_PIN_A)
            
            try:
                # First remove any existing event detection to avoid conflicts
                try:
                    GPIO.remove_event_detect(self.ROTARY_PIN_A)
                except:
                    pass
                GPIO.add_event_detect(self.ROTARY_PIN_A, GPIO.BOTH, 
                                    callback=self._on_rotary_rotated, 
                                    bouncetime=50)
                logger.debug(f"Added event detection for ROTARY_PIN_A (pin {self.ROTARY_PIN_A})")
            except Exception as e:
                logger.warning(f"Could not set up event detection for ROTARY_PIN_A: {str(e)}")
                
            try:
                try:
                    GPIO.remove_event_detect(self.ROTARY_BUTTON_PIN)
                except:
                    pass
                GPIO.add_event_detect(self.ROTARY_BUTTON_PIN, GPIO.FALLING, 
                                    callback=self._on_rotary_button_pressed, 
                                    bouncetime=300)
                logger.debug(f"Added event detection for ROTARY_BUTTON_PIN (pin {self.ROTARY_BUTTON_PIN})")
            except Exception as e:
                logger.warning(f"Could not set up event detection for ROTARY_BUTTON_PIN: {str(e)}")
                
            try:
                try:
                    GPIO.remove_event_detect(self.PRIMARY_SCHEDULE_PIN)
                except:
                    pass
                GPIO.add_event_detect(self.PRIMARY_SCHEDULE_PIN, GPIO.BOTH, 
                                    callback=self._on_switch_changed, 
                                    bouncetime=200)
                logger.debug(f"Added event detection for PRIMARY_SCHEDULE_PIN (pin {self.PRIMARY_SCHEDULE_PIN})")
            except Exception as e:
                logger.warning(f"Could not set up event detection for PRIMARY_SCHEDULE_PIN: {str(e)}")
                
            logger.info("GPIO setup completed successfully")
        except Exception as e:
            logger.error(f"Failed to setup GPIO: {str(e)}")

    def _on_rotary_rotated(self, channel: int) -> None:
        """Handle rotary encoder rotation for white noise volume control.
        
        Args:
            channel: GPIO channel that triggered the event
        """
        try:
            # Get current state of both encoder pins
            current_a = GPIO.input(self.ROTARY_PIN_A)
            current_b = GPIO.input(self.ROTARY_PIN_B)
            
            # Skip if no change in A pin state
            if current_a == self.last_encoder_state:
                return
                
            # Get current volume
            current_volume = self.audio_manager.get_volume()
            
            # Determine direction based on the state of both pins
            # If A and B are different, we're rotating clockwise
            # If A and B are the same, we're rotating counter-clockwise
            if current_a != current_b:
                # Clockwise rotation - increase volume by 5
                new_volume = min(100, current_volume + self.VOLUME_STEP)
                # Round to nearest 5
                new_volume = 5 * round(new_volume / 5)
                self.audio_manager.adjust_volume(new_volume)
                logger.info(f"Volume increased to {new_volume}%")
            else:
                # Counter-clockwise rotation - decrease volume by 5
                new_volume = max(0, current_volume - self.VOLUME_STEP)
                # Round to nearest 5
                new_volume = 5 * round(new_volume / 5)
                self.audio_manager.adjust_volume(new_volume)
                logger.info(f"Volume decreased to {new_volume}%")
            
            self.last_encoder_state = current_a
            
        except Exception as e:
            logger.error(f"Error in rotary encoder handling: {str(e)}")

    def _broadcast_volume_update(self, volume: int) -> None:
        """Broadcast volume update via WebSocket."""
        try:
            # Import here to avoid circular imports
            from backend.websocket_manager import web_socket_manager
            
            # Run the broadcast in a background task to avoid blocking
            asyncio.create_task(web_socket_manager.broadcast_volume_update(volume))
        except Exception as e:
            logger.error(f"Failed to broadcast volume update: {e}")

    def _on_rotary_button_pressed(self, channel: int) -> None:
        """Handle rotary encoder press for toggling white noise playback.
        
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
            
            return result
        except Exception as e:
            logger.error(f"Error handling rotary button press: {str(e)}")

    def _on_switch_changed(self, channel: int) -> None:
        """Set the schedule based on 3-state switch position.
        
        Switch positions:
        - OFF: Both pins LOW
        - A: Pin 1 HIGH, Pin 2 LOW
        - B: Pin 1 LOW, Pin 2 HIGH
        """
        try:
            from backend.settings_manager import ScheduleType
            
            # Read both switch pins
            pin1 = GPIO.input(self.PRIMARY_SCHEDULE_PIN)
            pin2 = GPIO.input(self.SECONDARY_SCHEDULE_PIN)
            
            # Determine schedule state
            if not pin1 and not pin2:
                schedule = ScheduleType.OFF.value
            elif pin1 and not pin2:
                schedule = ScheduleType.A.value
            elif not pin1 and pin2:
                schedule = ScheduleType.B.value
            else:
                logger.warning("Invalid switch state (both pins HIGH)")
                return
            
            # Update settings
            self.settings_manager.set_schedule(schedule)
            
            # Log and broadcast update
            logger.info(f"Schedule set to: {schedule} by switch (pin1={pin1}, pin2={pin2})")
            
        except Exception as e:
            logger.error(f"Error setting schedule: {str(e)}")

    def _cleanup(self) -> None:
        """Clean up GPIO resources."""
        try:
            GPIO.cleanup()
            logger.info("GPIO resources cleaned up successfully")
            
            # Broadcast system shutdown via WebSocket
            self._broadcast_shutdown()
        except Exception as e:
            logger.error(f"Error during GPIO cleanup: {str(e)}")
            raise
            
    def _broadcast_shutdown(self) -> None:
        """Broadcast system shutdown via WebSocket."""
        try:
            # Import here to avoid circular imports
            from backend.websocket_manager import web_socket_manager
            
            # Run the broadcast in a background task to avoid blocking
            asyncio.create_task(web_socket_manager.broadcast_shutdown())
        except Exception as e:
            logger.error(f"Failed to broadcast shutdown: {e}")

    # TODO add cleanup to exit and atexit.register(self.cleanup)
    def __del__(self) -> None:
        """Ensure cleanup on object destruction."""
        self._cleanup()

    def start_system(self) -> None:
        """Start the system and wait for events."""
        logger.info("Starting GPIO event handling system...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("GPIO system shutting down...")
            self._cleanup()

    def run(self) -> None:
        """Run the GPIO system in a separate thread."""
        system_thread = Thread(target=self.start_system, daemon=True)
        system_thread.start()
        logger.info("GPIO system thread started")
