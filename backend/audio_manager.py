import logging
import os
import random
import threading
from typing import Dict, List, Optional
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
        description="Default filename of the alarm sound (used as fallback)"
    )
    white_noise_sound: str = Field(
        "white_noise.mp3",
        description="Filename of the white noise sound"
    )
    sounds_dir: str = Field(
        "backend/sounds",
        description="Directory containing sound files"
    )
    alarm_sounds_dir: str = Field(
        "alarm_sounds",
        description="Subdirectory containing alarm sound files"
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
        self._alarm_sounds: List[str] = []
        
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
            # Load alarm sounds from the alarm_sounds directory
            alarm_sounds_path = os.path.join(self._config.sounds_dir, self._config.alarm_sounds_dir)
            if os.path.exists(alarm_sounds_path) and os.path.isdir(alarm_sounds_path):
                # Get all valid sound files in the alarm_sounds directory
                for filename in os.listdir(alarm_sounds_path):
                    # Skip files with .Identifier extension (these are Windows metadata files)
                    if filename.endswith('.mp3') and not filename.endswith('.Identifier'):
                        full_path = os.path.join(alarm_sounds_path, filename)
                        sound_key = f"alarm_{filename}"
                        self._sounds[sound_key] = pygame.mixer.Sound(full_path)
                        self._alarm_sounds.append(sound_key)
                        logger.info(f"Loaded alarm sound: {full_path}")
                
                if not self._alarm_sounds:
                    logger.warning(f"No alarm sounds found in {alarm_sounds_path}, using default")
                    # Load default alarm sound as fallback
                    alarm_path = os.path.join(self._config.sounds_dir, self._config.alarm_sound)
                    if os.path.exists(alarm_path):
                        self._sounds['alarm'] = pygame.mixer.Sound(alarm_path)
                        self._alarm_sounds.append('alarm')
                        logger.info(f"Loaded default alarm sound: {alarm_path}")
                    else:
                        logger.warning(f"Default alarm sound file not found: {alarm_path}")
                else:
                    logger.info(f"Loaded {len(self._alarm_sounds)} alarm sounds")
            else:
                logger.warning(f"Alarm sounds directory not found: {alarm_sounds_path}, using default")
                # Load default alarm sound as fallback
                alarm_path = os.path.join(self._config.sounds_dir, self._config.alarm_sound)
                if os.path.exists(alarm_path):
                    self._sounds['alarm'] = pygame.mixer.Sound(alarm_path)
                    self._alarm_sounds.append('alarm')
                    logger.info(f"Loaded default alarm sound: {alarm_path}")
                else:
                    logger.warning(f"Default alarm sound file not found: {alarm_path}")
            
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
        self._volume = max(0, min(volume, 70))
        
        if not self._mock_mode:
            # Convert 0-100 scale to 0.0-1.0 for pygame
            pygame_volume = self._volume / 100.0
            pygame.mixer.music.set_volume(pygame_volume)
            logger.debug(f"Set volume to {self._volume}%")

    def play_alarm(self) -> None:
        """
        Play a randomly selected alarm sound from the alarm_sounds directory.
        
        If an alarm is already playing, this will restart it with a potentially different sound.
        """
        with self._lock:
            if self._mock_mode:
                self._alarm_playing = True
                logger.info("Mock mode: Alarm started playing")
                return
                
            try:
                # Check if we have any alarm sounds loaded
                if not self._alarm_sounds:
                    logger.warning("No alarm sounds loaded")
                    return
                
                # Stop any currently playing alarm
                self.stop_alarm()
                
                # Randomly select an alarm sound from the loaded sounds
                selected_alarm_key = random.choice(self._alarm_sounds)
                
                # Play the selected alarm on a dedicated channel
                self._alarm_channel = pygame.mixer.find_channel()
                if self._alarm_channel:
                    self._alarm_channel.set_volume(self._volume / 100.0)
                    self._alarm_channel.play(self._sounds[selected_alarm_key], loops=-1)  # Loop indefinitely
                    logger.info(f"Alarm started playing: {selected_alarm_key}")
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

    def play_white_noise(self) -> bool:
        """
        Play white noise.
        
        If white noise is already playing, this will restart it.
        
        Returns:
            bool: True if white noise started successfully, False otherwise
        """
        with self._lock:
            if self._mock_mode:
                self._white_noise_playing = True
                logger.info("Mock mode: White noise started playing")
                return True
                
            try:
                # Validate sound is loaded
                if 'white_noise' not in self._sounds:
                    logger.error("White noise sound not loaded - cannot play")
                    self._white_noise_playing = False
                    return False
                    
                # Check if sound is valid
                if not self._sounds['white_noise']:
                    logger.error("White noise sound is invalid - cannot play")
                    self._white_noise_playing = False
                    return False
                
                # Stop any currently playing white noise
                self.stop_white_noise()
                
                # Play white noise on a dedicated channel
                self._white_noise_channel = pygame.mixer.find_channel()
                if self._white_noise_channel:
                    self._white_noise_channel.set_volume(self._volume / 100.0)
                    self._white_noise_channel.play(self._sounds['white_noise'], loops=-1)  # Loop indefinitely
                    self._white_noise_playing = True
                    logger.info("White noise started playing")
                    return True
                else:
                    logger.error("No available channel to play white noise - all channels in use")
                    self._white_noise_playing = False
                    return False
            except pygame.error as e:
                logger.error(f"Pygame error playing white noise: {str(e)}")
                self._white_noise_playing = False
                return False
            except Exception as e:
                logger.error(f"Failed to play white noise: {str(e)}")
                self._white_noise_playing = False
                return False

    def stop_white_noise(self) -> bool:
        """
        Stop the currently playing white noise.
        
        Returns:
            bool: True if white noise was stopped successfully, False otherwise
        """
        with self._lock:
            if self._mock_mode:
                self._white_noise_playing = False
                logger.info("Mock mode: White noise stopped")
                return True
                
            try:
                if self._white_noise_channel and self._white_noise_channel.get_busy():
                    self._white_noise_channel.stop()
                    logger.info("White noise stopped")
                self._white_noise_playing = False
                return True
            except pygame.error as e:
                logger.error(f"Pygame error stopping white noise: {str(e)}")
                return False
            except Exception as e:
                logger.error(f"Failed to stop white noise: {str(e)}")
                return False

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
            
            # Use the state tracking variable as the source of truth
            # but verify with the actual channel state when possible
            if not self._white_noise_playing:
                return False
                
            # Double-check with the actual channel state if available
            channel_playing = (self._white_noise_channel is not None and 
                              self._white_noise_channel.get_busy())
            
            # If there's a mismatch, update our state tracking
            if self._white_noise_playing and not channel_playing:
                logger.warning("White noise state mismatch detected - updating state")
                self._white_noise_playing = False
                
            return self._white_noise_playing

    def toggle_white_noise(self) -> bool:
        """
        Toggle white noise on/off.
        
        If white noise is playing, stop it. If not, start playing it.
        
        Returns:
            bool: True if operation was successful, False otherwise
        """
        with self._lock:
            if self.is_white_noise_playing():
                return self.stop_white_noise()
            else:
                return self.play_white_noise()
    
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
