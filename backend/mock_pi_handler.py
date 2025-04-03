"""Mock implementation of PiHandler for development environments."""

import logging
import time
from threading import Thread
from typing import Optional

from backend.audio_manager import AudioManager
from backend.settings_manager import SettingsManager

logger = logging.getLogger(__name__)

class MockPiHandler:
    """Mock implementation of PiHandler for development environments.
    
    This class mimics the behavior of the PiHandler class but doesn't
    require any Raspberry Pi hardware or GPIO libraries.
    """
    
    # Mock GPIO Pin Configuration (same as real PiHandler for consistency)
    GPIO_A = 26  # Rotary Encoder Pin A
    GPIO_B = 6   # Rotary Encoder Pin B
    BUTTON_PIN = 13  # Rotary Encoder Button
    SCHEDULE_PIN = 24  # Schedule Switch
    GLOBAL_PIN = 25  # Global Switch
    VOLUME_STEP = 0.05  # 5% volume adjustment step

    def __init__(self, settings_manager: SettingsManager, audio_manager: AudioManager):
        """Initialize MockPiHandler.
        
        Args:
            settings_manager: Manager for alarm and system settings
            audio_manager: Manager for audio playback and volume control
        """
        self.settings_manager = settings_manager
        self.audio_manager = audio_manager
        self.last_encoder_state = True  # Mock initial state
        
        # Log initialization
        logger.info("MockPiHandler initialized (development mode)")

    def _setup_gpio(self) -> None:
        """Mock GPIO setup."""
        logger.info("Mock GPIO setup completed")
        pass

    def _on_rotary_rotated(self, channel: int) -> None:
        """Mock rotary encoder rotation handler."""
        logger.debug(f"Mock rotary encoder rotated on channel {channel}")
        pass

    def _on_rotary_button_pressed(self, channel: int) -> None:
        """Mock rotary button press handler."""
        logger.debug(f"Mock rotary button pressed on channel {channel}")
        self.audio_manager.toggle_white_noise()

    def _toggle_primary_schedule(self, channel: int) -> None:
        """Mock schedule toggle handler."""
        logger.debug(f"Mock schedule toggle on channel {channel}")
        # Toggle between True and False
        current = self.settings_manager.get_is_primary_schedule()
        self.settings_manager.set_is_primary_schedule(not current)

    def _toggle_global_status(self, channel: int) -> None:
        """Mock global status toggle handler."""
        logger.debug(f"Mock global status toggle on channel {channel}")
        # Toggle between True and False
        current = self.settings_manager.get_is_global_on()
        self.settings_manager.set_is_global_on(not current)

    def cleanup(self) -> None:
        """Mock cleanup method."""
        logger.info("Mock GPIO resources cleaned up")
        pass

    def __del__(self) -> None:
        """Mock destructor."""
        self.cleanup()

    def start_system(self) -> None:
        """Mock system start method."""
        logger.info("Mock GPIO event handling system started")
        try:
            while True:
                time.sleep(60)  # Sleep longer in mock mode to reduce resource usage
        except KeyboardInterrupt:
            logger.info("Mock GPIO system shutting down...")
            self.cleanup()

    def run(self) -> None:
        """Run the mock GPIO system in a separate thread."""
        system_thread = Thread(target=self.start_system, daemon=True)
        system_thread.start()
        logger.info("Mock GPIO system thread started")

    # Additional methods for simulating hardware events in development mode
    
    def simulate_rotary_clockwise(self) -> None:
        """Simulate rotating the encoder clockwise."""
        self.audio_manager.adjust_volume(self.VOLUME_STEP)
        logger.info(f"Simulated volume increase: {self.audio_manager.get_volume():.0%}")
    
    def simulate_rotary_counterclockwise(self) -> None:
        """Simulate rotating the encoder counterclockwise."""
        self.audio_manager.adjust_volume(-self.VOLUME_STEP)
        logger.info(f"Simulated volume decrease: {self.audio_manager.get_volume():.0%}")
    
    def simulate_button_press(self) -> None:
        """Simulate pressing the rotary encoder button."""
        self._on_rotary_button_pressed(self.BUTTON_PIN)
        logger.info("Simulated button press (toggle white noise)")
    
    def simulate_schedule_toggle(self) -> None:
        """Simulate toggling the schedule switch."""
        self._toggle_primary_schedule(self.SCHEDULE_PIN)
        current = self.settings_manager.get_is_primary_schedule()
        logger.info(f"Simulated schedule toggle: {'Primary' if current else 'Secondary'}")
    
    def simulate_global_toggle(self) -> None:
        """Simulate toggling the global switch."""
        self._toggle_global_status(self.GLOBAL_PIN)
        current = self.settings_manager.get_is_global_on()
        logger.info(f"Simulated global toggle: {'On' if current else 'Off'}")
        
    # Methods to match the PiHandler interface for audio routes
    
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
