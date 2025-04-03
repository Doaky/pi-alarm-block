"""Dependency injection container for the Alarm Block application."""

from typing import Optional, Any
from fastapi import Depends
from functools import lru_cache
import logging
import os
import sys

from backend.alarm_manager import AlarmManager
from backend.settings_manager import SettingsManager
from backend.audio_manager import AudioManager
from backend.config import config, USE_PI_HARDWARE, DEV_MODE

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define PiHandler type for type hints
PiHandler = Any

# Import PiHandler or MockPiHandler based on configuration
if USE_PI_HARDWARE:
    try:
        # Attempt to import real PiHandler
        from backend.pi_handler import PiHandler
        logger.info("Using real Raspberry Pi hardware")
    except ImportError as e:
        logger.warning(f"Failed to import RPi.GPIO module: {e}")
        logger.warning("Falling back to mock implementation")
        # Import mock implementation if real one fails
        from backend.mock_pi_handler import MockPiHandler as PiHandler
else:
    # In development mode, use mock implementation
    from backend.mock_pi_handler import MockPiHandler as PiHandler
    logger.info("Using mock Pi hardware implementation (development mode)")


@lru_cache()
def get_settings_manager() -> SettingsManager:
    """Get or create SettingsManager instance."""
    return SettingsManager(str(config.data_dir))


@lru_cache()
def get_audio_manager() -> AudioManager:
    """Get or create AudioManager instance."""
    return AudioManager()


@lru_cache()
def get_pi_handler(
    settings_manager: SettingsManager = Depends(get_settings_manager),
    audio_manager: AudioManager = Depends(get_audio_manager)
) -> Optional[PiHandler]:
    """Get or create PiHandler instance."""
    try:
        return PiHandler(settings_manager, audio_manager)
    except Exception as e:
        logger.error(f"Failed to initialize Pi hardware: {e}")
        return None


@lru_cache()
def get_alarm_manager(
    settings_manager: SettingsManager = Depends(get_settings_manager),
    audio_manager: AudioManager = Depends(get_audio_manager),
    pi_handler: Optional[PiHandler] = Depends(get_pi_handler)
) -> AlarmManager:
    """Get or create AlarmManager instance."""
    return AlarmManager(settings_manager, audio_manager, pi_handler)
