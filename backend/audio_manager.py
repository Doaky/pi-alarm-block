import logging
import os
import threading
from typing import Dict, Optional
import pygame
from pygame import mixer
from pydantic import BaseModel, Field, validator

# Import config to check for development mode
from backend.config import DEV_MODE

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

    @validator('volume')
    def volume_must_be_valid(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Volume must be between 0 and 100')
        return v


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

        # Initialize state
        self._lock = threading.Lock()
        self._volume = self._config.volume
        
        # Check if we're in development mode
        if DEV_MODE:
            logger.info("Running in development mode - using mock audio implementation")
            # In development mode, we don't initialize pygame mixer
            self._mock_mode = True
            self._alarm_playing = False
            self._white_noise_playing = False
        else:
            # Only initialize pygame mixer when not in development mode
            self._mock_mode = False
            try:
                pygame.mixer.init()
                pygame.mixer.set_num_channels(8)  # Reserve channels for different sounds
                self._set_volume(self._config.volume)
                logger.info("Audio system initialized successfully")
                
                # Initialize pygame-specific state
                self._alarm_channel: Optional[pygame.mixer.Channel] = None
                self._white_noise_channel: Optional[pygame.mixer.Channel] = None
                self._sounds: Dict[str, pygame.mixer.Sound] = {}
                self._load_sounds()
            except Exception as e:
                logger.error(f"Failed to initialize audio system: {str(e)}")
                raise RuntimeError(f"Failed to initialize audio system: {str(e)}")

    def _load_sounds(self) -> None:
        """
        Load sound files into memory.
        
        Raises:
            RuntimeError: If sound files cannot be loaded
        """
        if self._mock_mode:
            return
            
        try:
            # Load alarm sound
            alarm_path = os.path.join(self._config.sounds_dir, self._config.alarm_sound)
            if os.path.exists(alarm_path):
                self._sounds['alarm'] = pygame.mixer.Sound(alarm_path)
                logger.info(f"Loaded alarm sound: {alarm_path}")
            else:
                logger.warning(f"Alarm sound file not found: {alarm_path}")
            
            # Load white noise sound
            white_noise_path = os.path.join(self._config.sounds_dir, self._config.white_noise_sound)
            if os.path.exists(white_noise_path):
                self._sounds['white_noise'] = pygame.mixer.Sound(white_noise_path)
                logger.info(f"Loaded white noise sound: {white_noise_path}")
            else:
                logger.warning(f"White noise sound file not found: {white_noise_path}")
        except Exception as e:
            logger.error(f"Failed to load sounds: {str(e)}")
            raise RuntimeError(f"Failed to load sounds: {str(e)}")

    def _set_volume(self, volume: int) -> None:
        """
        Set the volume level for all channels.
        
        Args:
            volume: Volume level (0-100)
        """
        self._volume = max(0, min(volume, 100))
        
        if not self._mock_mode:
            # Convert 0-100 scale to 0.0-1.0 for pygame
            pygame_volume = self._volume / 100.0
            pygame.mixer.music.set_volume(pygame_volume)
            logger.debug(f"Set volume to {self._volume}%")

    def play_alarm(self) -> None:
        """
        Play the alarm sound.
        
        If an alarm is already playing, this will restart it.
        """
        with self._lock:
            if self._mock_mode:
                self._alarm_playing = True
                logger.info("Mock mode: Alarm started playing")
                return
                
            try:
                if 'alarm' not in self._sounds:
                    logger.warning("Alarm sound not loaded")
                    return
                
                # Stop any currently playing alarm
                self.stop_alarm()
                
                # Play the alarm on a dedicated channel
                self._alarm_channel = pygame.mixer.find_channel()
                if self._alarm_channel:
                    self._alarm_channel.set_volume(self._volume / 100.0)
                    self._alarm_channel.play(self._sounds['alarm'], loops=-1)  # Loop indefinitely
                    logger.info("Alarm started playing")
                else:
                    logger.warning("No available channel to play alarm")
            except Exception as e:
                logger.error(f"Failed to play alarm: {str(e)}")

    def stop_alarm(self) -> None:
        """Stop the currently playing alarm."""
        with self._lock:
            if self._mock_mode:
                self._alarm_playing = False
                logger.info("Mock mode: Alarm stopped")
                return
                
            try:
                if self._alarm_channel and self._alarm_channel.get_busy():
                    self._alarm_channel.stop()
                    logger.info("Alarm stopped")
            except Exception as e:
                logger.error(f"Failed to stop alarm: {str(e)}")

    def play_white_noise(self) -> None:
        """
        Play white noise.
        
        If white noise is already playing, this will restart it.
        """
        with self._lock:
            if self._mock_mode:
                self._white_noise_playing = True
                logger.info("Mock mode: White noise started playing")
                return
                
            try:
                if 'white_noise' not in self._sounds:
                    logger.warning("White noise sound not loaded")
                    return
                
                # Stop any currently playing white noise
                self.stop_white_noise()
                
                # Play white noise on a dedicated channel
                self._white_noise_channel = pygame.mixer.find_channel()
                if self._white_noise_channel:
                    self._white_noise_channel.set_volume(self._volume / 100.0)
                    self._white_noise_channel.play(self._sounds['white_noise'], loops=-1)  # Loop indefinitely
                    logger.info("White noise started playing")
                else:
                    logger.warning("No available channel to play white noise")
            except Exception as e:
                logger.error(f"Failed to play white noise: {str(e)}")

    def stop_white_noise(self) -> None:
        """Stop the currently playing white noise."""
        with self._lock:
            if self._mock_mode:
                self._white_noise_playing = False
                logger.info("Mock mode: White noise stopped")
                return
                
            try:
                if self._white_noise_channel and self._white_noise_channel.get_busy():
                    self._white_noise_channel.stop()
                    logger.info("White noise stopped")
            except Exception as e:
                logger.error(f"Failed to stop white noise: {str(e)}")

    def adjust_volume(self, volume: int) -> None:
        """
        Adjust the volume level for all audio.
        
        Args:
            volume: Volume level (0-100)
        
        Raises:
            ValueError: If volume is outside the valid range
        """
        if not 0 <= volume <= 100:
            raise ValueError("Volume must be between 0 and 100")
        
        with self._lock:
            self._set_volume(volume)
            logger.info(f"Volume adjusted to {volume}%")

    def is_alarm_playing(self) -> bool:
        """Check if an alarm is currently playing."""
        with self._lock:
            if self._mock_mode:
                return self._alarm_playing
                
            return self._alarm_channel is not None and self._alarm_channel.get_busy()

    def is_white_noise_playing(self) -> bool:
        """Check if white noise is currently playing."""
        with self._lock:
            if self._mock_mode:
                return self._white_noise_playing
                
            return self._white_noise_channel is not None and self._white_noise_channel.get_busy()

    def get_volume(self) -> int:
        """Get the current volume level."""
        with self._lock:
            return self._volume

    def cleanup(self) -> None:
        """Clean up resources and stop all audio."""
        with self._lock:
            if self._mock_mode:
                self._alarm_playing = False
                self._white_noise_playing = False
                logger.info("Mock mode: Audio resources cleaned up")
                return
                
            try:
                # Stop all playback
                self.stop_alarm()
                self.stop_white_noise()
                
                # Clear sound resources
                self._sounds.clear()
                
                # Quit pygame mixer
                pygame.mixer.quit()
                logger.info("Audio resources cleaned up")
            except Exception as e:
                logger.error(f"Error during audio cleanup: {str(e)}")
