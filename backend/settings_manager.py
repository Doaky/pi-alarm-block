import json
import logging
import os
from typing import Dict, Optional, Literal
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

    class Config:
        json_schema_extra = {
            "example": {
                "schedule": "a"
            }
        }

class SettingsManager:
    """
    Manages alarm clock settings with persistence and validation.
    
    This class handles the storage and retrieval of global settings like
    schedule type and global alarm status. It ensures settings are properly
    validated and persisted to disk.
    """

    def __init__(self, file_path: str = "backend/data/settings.json"):
        """
        Initialize SettingsManager with storage path.
        
        Args:
            file_path: Path to the settings JSON file
        """
        self.file_path = file_path
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Load initial settings
        self._settings: Optional[Settings] = None
        self._load_settings()
        
        logger.info("SettingsManager initialized successfully")

    def _load_settings(self) -> None:
        """
        Load and validate settings from JSON file.
        
        If the file doesn't exist or is invalid, creates default settings.
        """
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r") as file:
                    data = json.load(file)
                    self._settings = Settings(**data)
                    logger.info("Settings loaded successfully")
            else:
                logger.info("No settings file found, using defaults")
                self._settings = Settings()
                self._save_settings()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in settings file: {str(e)}")
            self._settings = Settings()
            self._save_settings()
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            self._settings = Settings()
            self._save_settings()

    def _save_settings(self) -> None:
        """
        Save current settings to JSON file.
        
        Raises:
            IOError: If unable to write to the settings file
        """
        try:
            with open(self.file_path, "w") as file:
                json.dump(
                    self._settings.model_dump(),
                    file,
                    indent=4
                )
            logger.debug("Settings saved successfully")
        except Exception as e:
            logger.error(f"Failed to save settings: {str(e)}")
            raise IOError(f"Error saving settings: {str(e)}")

    def get_settings(self) -> Dict:
        """
        Get all current settings.
        
        Returns:
            dict: Dictionary containing all settings
        """
        return self._settings.model_dump()

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
                **self._settings.model_dump(),
                **settings
            })
            
            # If validation passes, update and save
            self._settings = new_settings
            self._save_settings()
            logger.info("Settings updated successfully")
        except Exception as e:
            logger.error(f"Failed to update settings: {str(e)}")
            raise ValueError(f"Invalid settings: {str(e)}")

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
        except Exception as e:
            logger.error(f"Failed to set schedule: {str(e)}")
            raise ValueError(f"Invalid schedule type: {str(e)}")

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

    def reset_to_defaults(self) -> None:
        """Reset all settings to their default values."""
        try:
            self._settings = Settings()
            self._save_settings()
            logger.info("Settings reset to defaults")
        except Exception as e:
            logger.error(f"Failed to reset settings: {str(e)}")
            raise
