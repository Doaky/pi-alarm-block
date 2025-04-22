import asyncio
import json
import logging
import os
import threading

from enum import Enum
from pydantic import BaseModel, Field

from backend.services.websocket_manager import web_socket_manager

# Configure logging
logger = logging.getLogger(__name__)

class ScheduleType(str, Enum):
    """Enum for schedule types"""
    A = "a"
    B = "b"
    OFF = "off"

class Settings(BaseModel):
    """Pydantic model for alarm clock settings validation."""
    schedule: ScheduleType = Field(
        ScheduleType.A,
        description="Current schedule setting: 'a' (primary), 'b' (secondary), or 'off' (disabled)"
    )
    volume: int = Field(
        25,  # Default to 25%
        ge=0,
        le=100,
        description="Current volume level (0-100)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "schedule": "a",
                "volume": 25
            }
        }

class SettingsManager:
    """
    Manages alarm clock settings.
    
    This class handles the storage and retrieval of global settings like
    schedule and volume.
    """
    def __init__(self):
        logger.info('SettingsManager __init__ starting')
        """
        Initialize SettingsManager with the project data directory.
        """
        # Thread lock for thread safety
        self._lock = threading.Lock()
        
        # Use the project data directory directly
        from backend.config import PROJECT_DATA_DIR
        self.data_dir = PROJECT_DATA_DIR
        self.file_path = self.data_dir / "settings.json"
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize settings
        self._settings = self._load_settings()
        
        logger.info("SettingsManager __init__ finished (initialized successfully)")

    def _load_settings(self) -> Settings:
        """Load settings from file."""
        with self._lock:
            try:
                if self.file_path.exists():
                    with open(self.file_path, 'r') as f:
                        data = json.load(f)
                    settings = Settings(**data)
                    logger.info("Settings loaded successfully")
                    return settings
                else:
                    logger.info("No settings file found, using defaults")
                    return Settings()
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
                return Settings()

    def _save_settings(self) -> None:
        """Save current settings to file."""
        # Make a copy of the settings under lock
        with self._lock:
            settings_data = self._settings.model_dump()
        try:
            # Write to temporary file first (atomic operation)
            temp_path = self.file_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(settings_data, f, indent=2)
            # Rename the temporary file to the target file (atomic on most filesystems)
            os.replace(temp_path, self.file_path)
            logger.info("Settings saved successfully")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            raise

    def get_schedule(self) -> str:
        """
        Get current schedule setting.
        
        Returns:
            str: Current schedule ('a', 'b', or 'off')
        """
        return self._settings.schedule.value

    def set_schedule(self, schedule: str) -> None:
        """
        Set schedule type.

        Args:
            schedule: Schedule type ('a', 'b', or 'off')

        Raises:
            ValueError: If the value is invalid
        """
        try:
            with self._lock:
                self._settings.schedule = ScheduleType(schedule)
                new_schedule = self._settings.schedule.value
            self._save_settings()  # No lock held
            logger.info(f"Schedule set to: {new_schedule}")
            asyncio.create_task(web_socket_manager.broadcast_schedule_update(new_schedule))
        except Exception as e:
            logger.error(f"Failed to set schedule: {e}")
            raise ValueError(f"Invalid schedule type: {e}")

    def get_volume(self) -> int:
        """
        Get current volume level.
        
        Returns:
            int: Current volume level (0-100)
        """
        return self._settings.volume
        
    def set_volume(self, volume: int) -> None:
        """
        Set volume level.
        
        Args:
            volume: Volume level (0-100)
            
        Raises:
            ValueError: If the value is outside the valid range
        """
        try:
            if not 0 <= volume <= 100:
                raise ValueError("Volume must be between 0 and 100")
            with self._lock:
                self._settings.volume = volume
            self._save_settings()  # No lock held
            logger.info(f"Volume set to: {volume}%")
            asyncio.create_task(web_socket_manager.broadcast_volume_update(volume))
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            raise ValueError(f"Invalid volume level: {e}")
