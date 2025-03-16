import json
import logging
import os
from typing import Dict, Optional
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

class Settings(BaseModel):
    """Pydantic model for alarm clock settings validation."""
    is_primary_schedule: bool = Field(
        True,
        description="Whether to use primary schedule (True) or secondary schedule (False)"
    )
    is_global_on: bool = Field(
        True,
        description="Whether alarms are globally enabled"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "is_primary_schedule": True,
                "is_global_on": True
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

    def get_is_primary_schedule(self) -> bool:
        """
        Get current schedule type.
        
        Returns:
            bool: True if primary schedule is active, False for secondary
        """
        return self._settings.is_primary_schedule

    def set_is_primary_schedule(self, is_primary: bool) -> None:
        """
        Set schedule type.
        
        Args:
            is_primary: True for primary schedule, False for secondary
            
        Raises:
            ValueError: If the value is invalid
        """
        try:
            self._settings.is_primary_schedule = is_primary
            self._save_settings()
            logger.info(f"Schedule type set to: {'primary' if is_primary else 'secondary'}")
        except Exception as e:
            logger.error(f"Failed to set schedule type: {str(e)}")
            raise ValueError(f"Invalid schedule type: {str(e)}")

    def get_is_global_on(self) -> bool:
        """
        Get global alarm status.
        
        Returns:
            bool: True if alarms are globally enabled
        """
        return self._settings.is_global_on

    def set_is_global_on(self, is_on: bool) -> None:
        """
        Set global alarm status.
        
        Args:
            is_on: True to enable alarms globally, False to disable
            
        Raises:
            ValueError: If the value is invalid
        """
        try:
            self._settings.is_global_on = is_on
            self._save_settings()
            logger.info(f"Global alarm status set to: {'enabled' if is_on else 'disabled'}")
        except Exception as e:
            logger.error(f"Failed to set global status: {str(e)}")
            raise ValueError(f"Invalid global status: {str(e)}")

    def reset_to_defaults(self) -> None:
        """Reset all settings to their default values."""
        try:
            self._settings = Settings()
            self._save_settings()
            logger.info("Settings reset to defaults")
        except Exception as e:
            logger.error(f"Failed to reset settings: {str(e)}")
            raise
