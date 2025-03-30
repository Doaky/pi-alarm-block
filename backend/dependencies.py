"""Dependency injection container for the Alarm Block application."""

from typing import Optional
from fastapi import Depends
from functools import lru_cache

from backend.alarm_manager import AlarmManager
from backend.settings_manager import SettingsManager
from backend.config import config

# Check for Raspberry Pi at module level
def is_raspberry_pi() -> bool:
    try:
        import RPi.GPIO
        return True
    except (RuntimeError, ModuleNotFoundError):
        return False

IS_RASPBERRY_PI = is_raspberry_pi()

if IS_RASPBERRY_PI:
    from backend.pi_handler import PiHandler


@lru_cache()
def get_settings_manager() -> SettingsManager:
    """Get or create SettingsManager instance."""
    return SettingsManager(str(config.data_dir / "settings.json"))


@lru_cache()
def get_pi_handler(
    settings_manager: SettingsManager = Depends(get_settings_manager)
) -> Optional[PiHandler]:
    """Get or create PiHandler instance if on Raspberry Pi."""
    if IS_RASPBERRY_PI:
        return PiHandler(settings_manager)
    return None


@lru_cache()
def get_alarm_manager(
    settings_manager: SettingsManager = Depends(get_settings_manager),
    pi_handler: Optional[PiHandler] = Depends(get_pi_handler)
) -> AlarmManager:
    """Get or create AlarmManager instance."""
    return AlarmManager(
        settings_manager,
        pi_handler,
        str(config.data_dir / "alarms.json")
    )
