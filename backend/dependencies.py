"""Dependency injection container for the Alarm Block application."""

from typing import Optional, Any, Dict
from fastapi import Depends
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

# Singleton instances
_instances: Dict[str, Any] = {}

# Define HardwareManager type for type hints
HardwareManager = Any

# Import HardwareManager or MockHardwareManager based on configuration
try:
    if USE_PI_HARDWARE:
        # Attempt to import real HardwareManager
        from hardware.hardware_manager import HardwareManager
        logger.info("Using real hardware implementation")
    else:
        logger.info("Hardware disabled by configuration")
        from hardware.mock_hardware_manager import MockHardwareManager as HardwareManager
except ImportError:
    logger.info("Using mock hardware implementation (development mode)")
    from hardware.mock_hardware_manager import MockHardwareManager as HardwareManager


def get_settings_manager() -> SettingsManager:
    """Get or create SettingsManager instance."""
    if 'settings_manager' not in _instances:
        logger.debug("Creating SettingsManager instance")
        _instances['settings_manager'] = SettingsManager()
    return _instances['settings_manager']


def get_audio_manager(settings_manager: SettingsManager = Depends(get_settings_manager)) -> AudioManager:
    if 'audio_manager' not in _instances:
        # Resolve actual SettingsManager instance
        _instances['audio_manager'] = AudioManager(
            settings_manager=settings_manager
        )
    return _instances['audio_manager']


def get_hardware_manager(
    settings_manager: SettingsManager = Depends(get_settings_manager),
    audio_manager: AudioManager = Depends(get_audio_manager)
) -> Optional[HardwareManager]:
    """Get or create HardwareManager instance."""
    if 'hardware_manager' not in _instances:
        try:
            logger.debug("Creating HardwareManager instance")
            _instances['hardware_manager'] = HardwareManager(settings_manager, audio_manager)
        except Exception as e:
            logger.error(f"Failed to initialize hardware: {e}")
            _instances['hardware_manager'] = None
    return _instances['hardware_manager']


def get_alarm_manager(
    settings_manager: SettingsManager = Depends(get_settings_manager),
    audio_manager: AudioManager = Depends(get_audio_manager),
    hardware_manager: Optional[HardwareManager] = Depends(get_hardware_manager)
) -> AlarmManager:
    """Get or create AlarmManager instance."""
    if 'alarm_manager' not in _instances:
        logger.debug("Creating AlarmManager instance")
        _instances['alarm_manager'] = AlarmManager(settings_manager, audio_manager, hardware_manager)
    return _instances['alarm_manager']
