import logging
import os
import threading
from typing import Dict, Optional
import pygame
from pygame import mixer
from pydantic import BaseModel, Field, validator

# Configure logging
logger = logging.getLogger(__name__)

class AudioConfig(BaseModel):
    """Pydantic model for audio configuration validation."""
    volume: int = Field(
        50,
        ge=0,
        le=100,
        description="Volume level (0-100)"
    )
    alarm_sound: str = Field(
        "alarm.mp3",
        description="Filename of the alarm sound"
    )
    white_noise_sound: str = Field(
        "white_noise.mp3",
        description="Filename of the white noise sound"
    )
    sounds_dir: str = Field(
        "backend/sounds",
        description="Directory containing sound files"
    )

    @validator('alarm_sound', 'white_noise_sound')
    def validate_sound_file(cls, v, values):
        """Validate that sound files exist."""
        if 'sounds_dir' in values:
            path = os.path.join(values['sounds_dir'], v)
            if not os.path.isfile(path):
                raise ValueError(f"Sound file not found: {path}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "volume": 50,
                "alarm_sound": "alarm.mp3",
                "white_noise_sound": "white_noise.mp3",
                "sounds_dir": "backend/sounds"
            }
        }

class AudioManager:
    """
    Manages audio playback and volume control with thread safety.
    
    This class handles playing alarm sounds and white noise, with proper
    resource management and thread-safe operations. It uses Pygame's mixer
    for audio playback and ensures clean initialization and shutdown.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize AudioManager with optional configuration.
        
        Args:
            config: Optional dictionary containing audio configuration
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If audio system initialization fails
        """
        # Initialize configuration
        try:
            self._config = AudioConfig(**(config or {}))
        except Exception as e:
            logger.error(f"Invalid audio configuration: {str(e)}")
            raise ValueError(f"Invalid audio configuration: {str(e)}")

        # Create sounds directory if it doesn't exist
        os.makedirs(self._config.sounds_dir, exist_ok=True)

        # Initialize Pygame mixer
        try:
            pygame.mixer.init()
            pygame.mixer.set_num_channels(8)  # Reserve channels for different sounds
            self._set_volume(self._config.volume)
            logger.info("Audio system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize audio system: {str(e)}")
            raise RuntimeError(f"Failed to initialize audio system: {str(e)}")

        # Initialize state
        self._lock = threading.Lock()
        self._alarm_channel: Optional[pygame.mixer.Channel] = None
        self._white_noise_channel: Optional[pygame.mixer.Channel] = None
        self._sounds: Dict[str, pygame.mixer.Sound] = {}
        self._load_sounds()

    def _load_sounds(self) -> None:
        """
        Load sound files into memory.
        
        Raises:
            RuntimeError: If sound loading fails
        """
        try:
            self._sounds['alarm'] = pygame.mixer.Sound(
                os.path.join(self._config.sounds_dir, self._config.alarm_sound)
            )
            self._sounds['white_noise'] = pygame.mixer.Sound(
                os.path.join(self._config.sounds_dir, self._config.white_noise_sound)
            )
            logger.debug("Sound files loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load sound files: {str(e)}")
            raise RuntimeError(f"Failed to load sound files: {str(e)}")

    def _set_volume(self, volume: int) -> None:
        """
        Set the global volume level.
        
        Args:
            volume: Volume level (0-100)
        """
        pygame.mixer.music.set_volume(volume / 100.0)

    def get_volume(self) -> int:
        """
        Get the current volume level.
        
        Returns:
            int: Current volume (0-100)
        """
        return self._config.volume

    def set_volume(self, volume: int) -> None:
        """
        Set the volume level with thread safety.
        
        Args:
            volume: Volume level (0-100)
            
        Raises:
            ValueError: If volume is out of range
        """
        try:
            with self._lock:
                self._config.volume = volume
                self._set_volume(volume)
            logger.debug(f"Volume set to {volume}")
        except Exception as e:
            logger.error(f"Failed to set volume: {str(e)}")
            raise ValueError(f"Invalid volume level: {str(e)}")

    def play_alarm(self) -> None:
        """
        Play the alarm sound with thread safety.
        
        The alarm sound will loop until explicitly stopped.
        
        Raises:
            RuntimeError: If playback fails
        """
        try:
            with self._lock:
                if self._alarm_channel and self._alarm_channel.get_busy():
                    logger.debug("Alarm already playing")
                    return

                self._alarm_channel = pygame.mixer.find_channel()
                if not self._alarm_channel:
                    raise RuntimeError("No available audio channels")

                self._alarm_channel.play(self._sounds['alarm'], loops=-1)
                logger.info("Alarm playback started")
        except Exception as e:
            logger.error(f"Failed to play alarm: {str(e)}")
            raise RuntimeError(f"Failed to play alarm: {str(e)}")

    def stop_alarm(self) -> None:
        """
        Stop the alarm sound with thread safety.
        """
        try:
            with self._lock:
                if self._alarm_channel:
                    self._alarm_channel.stop()
                    self._alarm_channel = None
                    logger.info("Alarm playback stopped")
        except Exception as e:
            logger.error(f"Error stopping alarm: {str(e)}")

    def play_white_noise(self) -> None:
        """
        Play white noise with thread safety.
        
        The white noise will loop until explicitly stopped.
        
        Raises:
            RuntimeError: If playback fails
        """
        try:
            with self._lock:
                if self._white_noise_channel and self._white_noise_channel.get_busy():
                    logger.debug("White noise already playing")
                    return

                self._white_noise_channel = pygame.mixer.find_channel()
                if not self._white_noise_channel:
                    raise RuntimeError("No available audio channels")

                self._white_noise_channel.play(self._sounds['white_noise'], loops=-1)
                logger.info("White noise playback started")
        except Exception as e:
            logger.error(f"Failed to play white noise: {str(e)}")
            raise RuntimeError(f"Failed to play white noise: {str(e)}")

    def stop_white_noise(self) -> None:
        """
        Stop white noise with thread safety.
        """
        try:
            with self._lock:
                if self._white_noise_channel:
                    self._white_noise_channel.stop()
                    self._white_noise_channel = None
                    logger.info("White noise playback stopped")
        except Exception as e:
            logger.error(f"Error stopping white noise: {str(e)}")

    def stop_all_sounds(self) -> None:
        """
        Stop all playing sounds with thread safety.
        """
        try:
            with self._lock:
                pygame.mixer.stop()
                self._alarm_channel = None
                self._white_noise_channel = None
                logger.info("All sound playback stopped")
        except Exception as e:
            logger.error(f"Error stopping all sounds: {str(e)}")

    def cleanup(self) -> None:
        """
        Clean up audio resources.
        
        This should be called when shutting down the application.
        """
        try:
            self.stop_all_sounds()
            pygame.mixer.quit()
            logger.info("Audio system cleaned up")
        except Exception as e:
            logger.error(f"Error during audio cleanup: {str(e)}")
