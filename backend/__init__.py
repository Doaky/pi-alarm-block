"""Alarm Block backend package.

This package contains the core components of the Alarm Block application:
- Alarm management and scheduling
- Audio playback and control
- Settings persistence
- WebSocket communication
- Hardware interaction (when in production mode)
"""

GREEN = "\033[32m"
RESET = "\033[0m"

print(GREEN + r"""
     __    __      __    ____  __  __    ____  __    _____   ___  _  _ 
    /__\  (  )    /__\  (  _ \(  \/  )  (  _ \(  )  (  _  ) / __)( )/ )
   /(__)\  )(__  /(__)\  )   / )    (    ) _ < )(__  )(_)( ( (__  )  ( 
  (__)(__)(____)(__)(__)(_)\_)(_/\/\_)  (____/(____)(_____) \___)(_)\_)
""" + RESET)

# Version management
__version__ = "0.1.0"

# Set up logging early
from backend.utils.logging import setup_logging
setup_logging()  # Initialize centralized logging

# Expose key classes for convenient imports
from backend.services.alarm_manager import AlarmManager
from backend.services.audio_manager import AudioManager
from backend.services.settings_manager import SettingsManager
from backend.services.websocket_manager import WebSocketManager
from backend.models.alarm import Alarm
from backend.config import Config

# Define public API
__all__ = [
    'AlarmManager',
    'AudioManager',
    'SettingsManager',
    'WebSocketManager',
    'Alarm',
    'Config',
    'get_version',
]

def get_version() -> str:
    """Return the current package version."""
    return __version__
