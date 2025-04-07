import json
import logging
import asyncio
from typing import Dict, Literal, Optional
from enum import Enum
from pydantic import BaseModel, Field

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
    Manages alarm clock settings with persistence and validation.
    
    This class handles the storage and retrieval of global settings like
    schedule type and global alarm status. It ensures settings are properly
    validated and persisted to disk.
    """
    def __init__(self):
        """
        Initialize SettingsManager with the project data directory.
        """
        # Use the project data directory directly
        from backend.config import PROJECT_DATA_DIR
        self.data_dir = PROJECT_DATA_DIR
        self.file_path = self.data_dir / "settings.json"
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize settings
        self._settings = self._load_settings()
        
        logger.info("SettingsManager initialized successfully")

    def _load_settings(self) -> Settings:
        """Load settings from file with validation."""
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
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self._settings.dict(), f, indent=2)
            logger.info("Settings saved successfully")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            raise

    def get_settings(self) -> Dict:
        """
        Get all current settings.
        
        Returns:
            dict: Dictionary containing all settings
        """
        return self._settings.dict()

    def update_settings(self, settings: Dict) -> None:
        """
        Update multiple settings at once.
        
        Args:
            settings: Dictionary of settings to update
            
        Raises:
            ValueError: If settings are invalid
        """
        try:
            # Create new settings object with updates
            new_settings = Settings(**{
                **self._settings.dict(),
                **settings
            })
            
            # If validation passes, update and save
            self._settings = new_settings
            self._save_settings()
            logger.info("Settings updated successfully")
        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            raise ValueError(f"Invalid settings: {e}")

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
            self._settings.schedule = ScheduleType(schedule)
            self._save_settings()
            logger.info(f"Schedule set to: {schedule}")
            
            # Broadcast the schedule change via WebSocket
            self._broadcast_schedule_update()
        except Exception as e:
            logger.error(f"Failed to set schedule: {e}")
            raise ValueError(f"Invalid schedule type: {e}")

    def get_is_primary_schedule(self) -> bool:
        """
        Get current schedule type (legacy compatibility).
        
        Returns:
            bool: True if primary schedule is active (schedule='a'), False otherwise
        """
        return self._settings.schedule == ScheduleType.A

    def get_is_global_on(self) -> bool:
        """
        Get global alarm status (legacy compatibility).
        
        Returns:
            bool: True if alarms are globally enabled (schedule != 'off')
        """
        return self._settings.schedule != ScheduleType.OFF

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
                
            self._settings.volume = volume
            self._save_settings()
            logger.info(f"Volume set to: {volume}%")
            
            # Broadcast the volume change via WebSocket
            self._broadcast_volume_update(volume)
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            raise ValueError(f"Invalid volume level: {e}")
            
    def reset_to_defaults(self) -> None:
        """Reset all settings to their default values."""
        try:
            self._settings = Settings()
            self._save_settings()
            logger.info("Settings reset to defaults")
            
            # Broadcast all setting updates
            self._broadcast_schedule_update()
            self._broadcast_volume_update(self._settings.volume)
        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            raise
            
    def _broadcast_schedule_update(self) -> None:
        """Broadcast schedule update via WebSocket."""
        try:
            # Import here to avoid circular imports
            from backend.websocket_manager import connection_manager
            
            # Run the broadcast in a background task to avoid blocking
            asyncio.create_task(connection_manager.broadcast_schedule_update(
                self.get_schedule()
            ))
        except Exception as e:
            logger.error(f"Failed to broadcast schedule update: {e}")
    
    def _broadcast_volume_update(self, volume: int) -> None:
        """Broadcast volume update via WebSocket."""
        try:
            # Import here to avoid circular imports
            from backend.websocket_manager import connection_manager
            
            # Run the broadcast in a background task to avoid blocking
            asyncio.create_task(connection_manager.broadcast_volume_update(volume))
        except Exception as e:
            logger.error(f"Failed to broadcast volume update: {e}")
