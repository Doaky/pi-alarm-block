import asyncio
import logging
import time
from threading import Thread

from backend.services.audio_manager import AudioManager
from backend.services.settings_manager import SettingsManager

logger = logging.getLogger(__name__)

class MockHardwareManager:
    """Mock implementation of HardwareManager for development environments.
    
    This class mimics the behavior of the HardwareManager class but doesn't
    require any specific hardware or GPIO libraries.
    """
    
    # GPIO Pin Constants - match the real HardwareManager
    ROTARY_PIN_A = 26  # Rotary Encoder Pin A
    ROTARY_PIN_B = 6  # Rotary Encoder Pin B
    ROTARY_BUTTON_PIN = 13  # Rotary Encoder Button

    PRIMARY_SCHEDULE_PIN = 24  # Primary Schedule Switch Pin
    SECONDARY_SCHEDULE_PIN = 25  # Secondary Schedule Switch Pin
    GLOBAL_PIN = 27  # Global Switch

    # Constants
    VOLUME_STEP = 5  # 5% volume adjustment step

    def __init__(self, settings_manager: SettingsManager, audio_manager: AudioManager):
        """Initialize MockHardwareManager.
        
        Args:
            settings_manager: Manager for alarm and system settings
            audio_manager: Manager for audio playback and volume control
        """
        self.settings_manager = settings_manager
        self.audio_manager = audio_manager
        self.last_encoder_state = True  # Mock initial state
        
        # Log initialization
        logger.info("MockHardwareManager initialized (development mode)")

    def _setup_gpio(self) -> None:
        """Mock GPIO setup."""
        logger.info("Mock GPIO setup completed")
        pass

    def _on_rotary_rotated(self, channel: int) -> None:
        """Mock rotary encoder rotation handler for white noise volume control.
        
        Args:
            channel: GPIO channel that triggered the event
        """
        logger.debug(f"Mock rotary encoder rotated on channel {channel}")
        # In a real implementation, this would read the encoder state and adjust volume
        # For mock, we'll just simulate a random direction
        import random
        if random.choice([True, False]):
            self.audio_manager.adjust_volume(self.VOLUME_STEP)
            logger.info(f"Mock volume increased to {self.audio_manager.get_volume()}%")
        else:
            self.audio_manager.adjust_volume(-self.VOLUME_STEP)
            logger.info(f"Mock volume decreased to {self.audio_manager.get_volume()}%")
            
        # Broadcast the volume update
        self._broadcast_volume_update(self.audio_manager.get_volume())

    def _on_rotary_button_pressed(self, channel: int) -> None:
        """Mock rotary encoder press for toggling white noise playback.
        
        Args:
            channel: GPIO channel that triggered the event
        """
        try:
            logger.debug(f"Mock rotary button pressed on channel {channel}")
            
            # Check if white noise is currently playing
            was_playing = self.audio_manager.is_white_noise_playing()
            
            # Toggle white noise
            result = self.audio_manager.toggle_white_noise()
            
            # Log the action with clear status
            if was_playing:
                logger.info("White noise turned OFF by mock rotary button press")
            else:
                logger.info("White noise turned ON by mock rotary button press")
            
            return result
        except Exception as e:
            logger.error(f"Error handling mock rotary button press: {str(e)}")

    def _on_switch_changed(self, channel: int) -> None:
        """Set the schedule based on 3-state switch position.
        
        Switch positions:
        - OFF: Both pins LOW
        - A: Pin 1 HIGH, Pin 2 LOW
        - B: Pin 1 LOW, Pin 2 HIGH
        """
        try:
            from backend.settings_manager import ScheduleType
            
            logger.debug(f"Mock schedule toggle on channel {channel}")
            
            # Simulate reading both switch pins
            # For mock, we'll just cycle through the states
            current_schedule = self.settings_manager.get_schedule()
            
            if current_schedule == ScheduleType.OFF.value:
                schedule = ScheduleType.A.value
                pin1, pin2 = True, False
            elif current_schedule == ScheduleType.A.value:
                schedule = ScheduleType.B.value
                pin1, pin2 = False, True
            else:  # B or any other state
                schedule = ScheduleType.OFF.value
                pin1, pin2 = False, False
            
            # Update settings
            self.settings_manager.set_schedule(schedule)
            
            # Log and broadcast update
            logger.info(f"Mock schedule set to: {schedule} by switch (pin1={pin1}, pin2={pin2})")
            
        except Exception as e:
            logger.error(f"Error setting mock schedule: {str(e)}")

    def _cleanup(self) -> None:
        """Clean up mock GPIO resources."""
        try:
            logger.info("Mock GPIO resources cleaned up successfully")
            
            # Broadcast system shutdown via WebSocket
            self._broadcast_shutdown()
        except Exception as e:
            logger.error(f"Error during mock GPIO cleanup: {str(e)}")

    def __del__(self) -> None:
        """Mock destructor."""
        self._cleanup()

    def start_system(self) -> None:
        """Mock system start method."""
        logger.info("Mock GPIO event handling system started")
        try:
            while True:
                time.sleep(60)  # Sleep longer in mock mode to reduce resource usage
        except KeyboardInterrupt:
            logger.info("Mock GPIO system shutting down...")
            self._cleanup()

    def run(self) -> None:
        """Run the mock GPIO system in a separate thread."""
        system_thread = Thread(target=self.start_system, daemon=True)
        system_thread.start()
        logger.info("Mock GPIO system thread started")

    # Additional methods for simulating hardware events in development mode
    
    def simulate_rotary_clockwise(self) -> None:
        """Simulate rotating the encoder clockwise."""
        self.audio_manager.adjust_volume(self.VOLUME_STEP)
        volume = self.audio_manager.get_volume()
        logger.info(f"Simulated volume increase: {volume}%")
        self._broadcast_volume_update(volume)
    
    def simulate_rotary_counterclockwise(self) -> None:
        """Simulate rotating the encoder counterclockwise."""
        self.audio_manager.adjust_volume(-self.VOLUME_STEP)
        volume = self.audio_manager.get_volume()
        logger.info(f"Simulated volume decrease: {volume}%")
        self._broadcast_volume_update(volume)
    
    def simulate_button_press(self) -> None:
        """Simulate pressing the rotary encoder button."""
        self._on_rotary_button_pressed(self.ROTARY_BUTTON_PIN)
        logger.info("Simulated button press (toggle white noise)")
    
    def simulate_schedule_toggle(self) -> None:
        """Simulate toggling the schedule switch."""
        self._on_switch_changed(self.PRIMARY_SCHEDULE_PIN)
        current = self.settings_manager.get_schedule()
        logger.info(f"Simulated schedule toggle: {current}")
    
    def simulate_global_toggle(self) -> None:
        """Simulate toggling the global switch."""
        # TODO: Implement global switch toggle when added to HardwareManager
        logger.info("Simulated global toggle (not implemented in HardwareManager yet)")
        
    # Methods to match the HardwareManager interface for audio routes
    
    def play_alarm(self) -> None:
        """Simulate playing an alarm."""
        logger.info("Mock: Playing alarm sound")
        self.audio_manager.play_alarm()
    
    def stop_alarm(self) -> None:
        """Simulate stopping an alarm."""
        logger.info("Mock: Stopping alarm sound")
        self.audio_manager.stop_alarm()
    
    def play_white_noise(self) -> None:
        """Simulate playing white noise."""
        logger.info("Mock: Playing white noise")
        self.audio_manager.play_white_noise()
    
    def stop_white_noise(self) -> None:
        """Simulate stopping white noise."""
        logger.info("Mock: Stopping white noise")
        self.audio_manager.stop_white_noise()

    def _broadcast_volume_update(self, volume: int) -> None:
        """Broadcast volume update via WebSocket."""
        try:
            # Import here to avoid circular imports
            from backend.websocket_manager import web_socket_manager
            
            # Run the broadcast in a background task to avoid blocking
            asyncio.create_task(web_socket_manager.broadcast_volume_update(volume))
        except Exception as e:
            logger.error(f"Failed to broadcast volume update: {e}")
            
    def _broadcast_shutdown(self) -> None:
        """Broadcast system shutdown via WebSocket."""
        try:
            # Import here to avoid circular imports
            from backend.websocket_manager import web_socket_manager
            
            # Run the broadcast in a background task to avoid blocking
            asyncio.create_task(web_socket_manager.broadcast_shutdown())
        except Exception as e:
            logger.error(f"Failed to broadcast shutdown: {e}")
