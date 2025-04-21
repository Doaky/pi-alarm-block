"""Dependency injection container for the Alarm Block application."""

from typing import Optional, Any, Dict
from fastapi import Depends

from backend.services.alarm_manager import AlarmManager
from backend.services.settings_manager import SettingsManager
from backend.services.audio_manager import AudioManager
from backend.config import USE_PI_HARDWARE, DEV_MODE
from backend.utils.logging import get_logger

# Get module logger
logger = get_logger(__name__)

# Singleton instances
_instances: Dict[str, Any] = {}

# Define HardwareManager type for type hints
HardwareManager = Any

# Import HardwareManager or MockHardwareManager based on configuration
try:
    if USE_PI_HARDWARE:
        # Attempt to import real HardwareManager
        from hardware.hardware_manager import HardwareManager
        logger.debug("Using real hardware implementation")
    else:
        logger.debug("Hardware disabled by configuration")
        from hardware.mock_hardware_manager import MockHardwareManager as HardwareManager
except ImportError:
    logger.debug("Using mock hardware implementation (development mode)")
    from hardware.mock_hardware_manager import MockHardwareManager as HardwareManager


def get_settings_manager() -> SettingsManager:
    """Get or create SettingsManager instance."""
    if 'settings_manager' not in _instances:
        logger.debug("Creating SettingsManager instance", extra={"action": "get_settings_manager"})
        _instances['settings_manager'] = SettingsManager()
    return _instances['settings_manager']


def get_audio_manager(settings_manager: SettingsManager = Depends(get_settings_manager)) -> AudioManager:
    """Get or create AudioManager instance."""
    if 'audio_manager' not in _instances:
        logger.debug("Creating AudioManager instance", extra={"action": "get_audio_manager"})
        # if not pi hardware, use mock audio manager
        if not USE_PI_HARDWARE:
            from backend.services.audio_helpers.mock_audio_manager import MockAudioManager
            _instances['audio_manager'] = MockAudioManager(settings_manager=settings_manager)
            return _instances['audio_manager']
        
        _instances['audio_manager'] = AudioManager(settings_manager=settings_manager)
    return _instances['audio_manager']


def get_hardware_manager(
    settings_manager: SettingsManager = Depends(get_settings_manager),
    audio_manager: AudioManager = Depends(get_audio_manager)
) -> Optional[HardwareManager]:
    """Get or create HardwareManager instance."""
    if 'hardware_manager' not in _instances:
        try:
            logger.debug("Creating HardwareManager instance", extra={"action": "get_hardware_manager"})
            _instances['hardware_manager'] = HardwareManager(settings_manager, audio_manager)
        except Exception as e:
            logger.error(f"Failed to initialize hardware: {e}", extra={"action": "get_hardware_manager", "error": str(e)})
            _instances['hardware_manager'] = None
    return _instances['hardware_manager']


# This function is used by FastAPI for dependency injection
def get_alarm_manager(
    settings_manager: SettingsManager = Depends(get_settings_manager),
    audio_manager: AudioManager = Depends(get_audio_manager),
    hardware_manager: Optional[HardwareManager] = Depends(get_hardware_manager)
) -> AlarmManager:
    """Get the AlarmManager instance for dependency injection.
    
    This function avoids exposing type annotations that could confuse FastAPI's
    response model generation. It internally uses the proper dependencies
    but presents a clean interface to FastAPI.
    
    Returns:
        AlarmManager: The singleton AlarmManager instance
    """
    # Get dependencies manually to avoid FastAPI type inference issues
    # settings_manager = get_settings_manager()
    # audio_manager = get_audio_manager(settings_manager)
    # hardware_manager = get_hardware_manager(settings_manager, audio_manager)
    
    # Get or create AlarmManager instance
    if 'alarm_manager' not in _instances:
        logger.debug("Creating AlarmManager instance", extra={"action": "get_alarm_manager"})
        _instances['alarm_manager'] = AlarmManager(settings_manager, audio_manager, hardware_manager)
    return _instances['alarm_manager']
