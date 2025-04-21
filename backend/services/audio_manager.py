import os
import threading
import time
from typing import Dict, Optional

import pygame
from pydantic import BaseModel, Field, field_validator

from backend.utils.logging import get_logger
from backend.services.audio_helpers.alarm_audio import AlarmAudio
from backend.services.audio_helpers.white_noise import WhiteNoiseAudio
from backend.services.settings_manager import SettingsManager

# Get logger for this module
logger = get_logger(__name__)

class AudioConfig(BaseModel):
    """Pydantic model for audio configuration validation."""
    volume: int = Field(
        50,
        ge=0,
        le=100,
        description="Volume level for white noise (0-100)"
    )
    alarm_volume: int = Field(
        75,
        ge=0,
        le=100,
        description="Alarm volume level (0-100)"
    )
    alarm_sound: str = Field(
        "default_alarm.ogg",
        description="Default filename of the alarm sound (used as fallback)"
    )
    white_noise_sound: str = Field(
        "white_noise.ogg",
        description="Filename of the white noise sound"
    )
    sounds_dir: str = Field(
        "backend/data/sounds",
        description="Directory containing sound files"
    )
    alarm_sounds_dir: str = Field(
        "alarms",
        description="Subdirectory containing alarm sound files"
    )

    @field_validator('volume', 'alarm_volume')
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

    def __init__(self, config: Optional[Dict] = None, settings_manager: Optional[SettingsManager] = None):
        logger.info('AudioManager __init__ starting')
        """
        Initialize AudioManager with optional configuration.
        
        Args:
            config: Optional dictionary containing audio configuration
            settings_manager: Optional settings manager for volume persistence
            
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
        
        # Create alarm sounds directory if it doesn't exist
        alarm_sounds_path = os.path.join(self._config.sounds_dir, self._config.alarm_sounds_dir)
        os.makedirs(alarm_sounds_path, exist_ok=True)

        # Initialize state
        self._lock = threading.Lock()
        self._settings_manager = settings_manager
        
        # Get volume from settings if available, otherwise use default
        if self._settings_manager is not None:
            self._volume = self._settings_manager.get_volume()
            logger.debug(f"Loaded volume from settings: {self._volume}%")
        else:
            self._volume = self._config.volume
            logger.debug(f"Using default volume: {self._volume}%")
            
        # Initialize separate volume controls
        self._alarm_volume = self._config.alarm_volume
        self._previous_volume = self._volume  # For restoring white noise volume after alarm
        
        # Initialize pygame mixer
        logger.info("Initializing audio system")
        try:
            # Initialize with a higher frequency and buffer size to reduce popping
            # For Raspberry Pi, we need to ensure the audio device is properly initialized
            # Set the SDL_AUDIODRIVER environment variable to ensure proper audio device selection
            os.environ['SDL_AUDIODRIVER'] = 'alsa'
            
            # Initialize pygame
            pygame.init()
            
            # Initialize mixer with more conservative settings for Raspberry Pi
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            pygame.mixer.set_num_channels(8)  # Reserve channels for different sounds
            
            # Set the volume directly
            pygame.mixer.music.set_volume(self._volume / 100.0)
            
            # Play a short, silent sound to initialize the audio system properly
            # This helps prevent the initial pop sound
            self._init_audio_system()
            
            logger.info("Audio system initialized successfully")
            
            # Initialize shared sound dictionary
            self._sounds: Dict[str, pygame.mixer.Sound] = {}
            
            # Initialize helper classes
            self._alarm_audio = AlarmAudio(
                sounds_dir=self._config.sounds_dir,
                alarm_sounds_dir=self._config.alarm_sounds_dir,
                sounds=self._sounds,
                alarm_volume=self._alarm_volume,
                lock=self._lock
            )
            
            self._white_noise_audio = WhiteNoiseAudio(
                sounds_dir=self._config.sounds_dir,
                white_noise_sound=self._config.white_noise_sound,
                sounds=self._sounds,
                volume=self._volume,
                settings_manager=self._settings_manager,
                lock=self._lock
            )
            
            logger.info("AudioManager __init__ finished (audio helpers initialized successfully)")
            
        except Exception as e:
            logger.error(f"Failed to initialize audio system: {str(e)}")
            raise RuntimeError(f"Failed to initialize audio system: {str(e)}")

    # Sound loading is now handled by the helper classes

    def play_alarm(self) -> bool:
        """
        Play alarm sound. This will stop white noise if it's playing.
        
        Returns:
            bool: True if operation was successful, False otherwise
        """
        # Delegate to AlarmAudio with reference to WhiteNoiseAudio to stop white noise
        return self._alarm_audio.play_alarm(
            white_noise_audio=self._white_noise_audio
        )

    def stop_alarm(self) -> None:
        """
        Stop the currently playing alarm sound.
        """
        # Delegate to AlarmAudio
        self._alarm_audio.stop_alarm()

    def play_white_noise(self) -> bool:
        """
        Play white noise sound.
        
        Returns:
            bool: True if operation was successful, False otherwise
        """
        # Delegate to WhiteNoiseAudio with callback to check if alarm is playing
        return self._white_noise_audio.play_white_noise(
            is_alarm_playing_callback=self._alarm_audio.is_alarm_playing
        )

    def stop_white_noise(self) -> None:
        """
        Stop the currently playing white noise sound.
        """
        # Delegate to WhiteNoiseAudio
        self._white_noise_audio.stop_white_noise()

    def adjust_volume(self, volume: int) -> None:
        """
        Adjust the master volume level for white noise.
        The master volume is saved to settings and affects white noise only.
        Alarm volume remains separate and is not affected by this setting.
        
        Args:
            volume: Volume level (0-100)
        
        Raises:
            ValueError: If volume is outside the valid range
        """
        # Delegate to WhiteNoiseAudio
        self._white_noise_audio.adjust_volume(volume)

    def is_alarm_playing(self) -> bool:
        """Check if an alarm is currently playing."""
        return self._alarm_audio.is_alarm_playing()

    def is_white_noise_playing(self) -> bool:
        """Check if white noise is currently playing."""
        return self._white_noise_audio.is_white_noise_playing()

    def toggle_white_noise(self) -> bool:
        """
        Toggle white noise on/off.
        
        If white noise is playing, stop it. If not, start playing it.
        
        Returns:
            bool: True if operation was successful, False otherwise
        """
        if self.is_white_noise_playing():
            return self.stop_white_noise()
        else:
            return self.play_white_noise()

    def get_volume(self) -> int:
        """Get the current master volume level."""
        return self._white_noise_audio.get_volume()

    def get_white_noise_volume(self) -> int:
        """Get the current white noise volume level."""
        if self.is_white_noise_playing() and self._white_noise_audio.white_noise_channel:
            try:
                return int(self._white_noise_audio.white_noise_channel.get_volume() * 100)
            except Exception:
                pass
        return self.get_volume()

    def get_alarm_volume(self) -> int:
        """Get the current alarm volume level."""
        return self._alarm_audio.get_alarm_volume()

    def set_alarm_volume(self, volume: int) -> None:
        """Set the alarm volume level."""
        # Validate volume range
        if not 0 <= volume <= 100:
            raise ValueError("Volume must be between 0 and 100")
            
        self._alarm_audio.set_alarm_volume(volume)
            
        # Apply to alarm channel if active (outside lock)
        if self.is_alarm_playing() and self._alarm_audio.alarm_channel:
            try:
                self._alarm_audio.alarm_channel.set_volume(volume / 100.0)
            except Exception as e:
                logger.error(f"Error setting alarm volume: {e}")
                    
        logger.info(f"Alarm volume set to {volume}%")

    def _init_audio_system(self) -> None:
        """Initialize audio system with a silent buffer to prevent popping."""
        try:
            # Create a short silent sound buffer
            silent_buffer = pygame.mixer.Sound(buffer=bytes(bytearray(1024)))
            # Play it at zero volume to initialize the audio system
            silent_channel = pygame.mixer.Channel(0)
            silent_channel.set_volume(0.0)
            silent_channel.play(silent_buffer)
            # Wait a short time for the system to stabilize
            time.sleep(0.1)
            silent_channel.stop()
            logger.debug("Audio system pre-initialized with silent buffer")
        except Exception as e:
            logger.warning(f"Could not pre-initialize audio system: {str(e)}")

    def cleanup(self) -> None:
        """Clean up resources and stop all audio."""
        try:
            # Stop any playing sounds
            if self.is_white_noise_playing():
                self.stop_white_noise()
                
            if self.is_alarm_playing():
                self.stop_alarm()
                
            # Unload all sounds
            self._sounds = {}
            
            # Quit pygame mixer if it's initialized
            if pygame.mixer.get_init():
                pygame.mixer.quit()
                logger.info("Pygame mixer quit")
                
        except Exception as e:
            logger.error(f"Error during audio cleanup: {str(e)}")
