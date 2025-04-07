import os
import random
import threading
import time
from typing import Dict, List, Optional
import pygame
from pydantic import BaseModel, Field, field_validator
import asyncio
import logging

# Import settings manager for volume persistence
from backend.settings_manager import SettingsManager

# Import config to check for development mode
from backend.config import DEV_MODE

# Import centralized logging utility
from backend.utils.logging import setup_logging

# Configure logger with colored output
logger = setup_logging(level="INFO", module_name=__name__)

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
        
        # Initialize playback state variables
        self._alarm_playing = False
        self._white_noise_playing = False
        self._alarm_sounds: List[str] = []
        
        # Check if we're in development mode
        if DEV_MODE:
            logger.info("Running in development mode - using mock audio implementation")
            # In development mode, we don't initialize pygame mixer
            self._mock_mode = True
        else:
            # Only initialize pygame mixer when not in development mode
            self._mock_mode = False
            try:
                # Initialize with a higher frequency and buffer size to reduce popping
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
                pygame.mixer.set_num_channels(8)  # Reserve channels for different sounds
                # Set the volume directly instead of using the removed _set_volume method
                pygame.mixer.music.set_volume(self._volume / 100.0)
                
                # Play a short, silent sound to initialize the audio system properly
                # This helps prevent the initial pop sound
                self._init_audio_system()
                
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
            # Get all valid sound files in the alarm_sounds directory
            for filename in os.listdir(alarm_sounds_path):
                # Skip files with .Identifier extension (these are Windows metadata files)
                if filename.endswith('.ogg') and not filename.endswith('.Identifier'):
                    full_path = os.path.join(alarm_sounds_path, filename)
                    sound_key = f"alarm_{filename}"
                    self._sounds[sound_key] = pygame.mixer.Sound(full_path)
                    self._alarm_sounds.append(sound_key)
                    logger.info(f"Loaded alarm sound: {full_path}")
            
            # Check if we found any alarm sounds
            if not self._alarm_sounds:
                logger.warning(f"No alarm sounds found in {alarm_sounds_path}, using default")
                # Load default alarm sound as fallback
                self._load_default_alarm_sound()
            else:
                logger.info(f"Loaded {len(self._alarm_sounds)} alarm sounds")
            
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
        
        
    def _load_default_alarm_sound(self) -> None:
        """
        Load the default alarm sound as fallback.
        """
        # Load default alarm sound from the sounds directory
        alarm_path = os.path.join(self._config.sounds_dir, self._config.alarm_sound)
        if os.path.exists(alarm_path):
            self._sounds['alarm'] = pygame.mixer.Sound(alarm_path)
            self._alarm_sounds.append('alarm')
            logger.info(f"Loaded default alarm sound: {alarm_path}")
        else:
            logger.warning(f"Default alarm sound file not found: {alarm_path}")



    def play_alarm(self) -> None:
        """
        Play a randomly selected alarm sound from the alarm_sounds directory.
        
        If an alarm is already playing, this will restart it with a potentially different sound.
        If white noise is playing, it will be temporarily lowered in volume.
        """
        # Handle mock mode with minimal locking
        if self._mock_mode:
            with self._lock:
                self._alarm_playing = True
                logger.info("Mock mode: Alarm started playing")
            # Broadcast alarm status update
            self._broadcast_alarm_status(True)
            return
        
        # Check if we have any alarm sounds loaded
        alarm_sounds = None
        with self._lock:
            alarm_sounds = self._alarm_sounds.copy() if self._alarm_sounds else []
            # Store current volume for later restoration
            if self._white_noise_playing:
                self._previous_volume = self._volume
            
        if not alarm_sounds:
            logger.warning("No alarm sounds loaded")
            return
        
        try:
            # Stop any currently playing alarm (handles its own locking)
            self.stop_alarm()
            
            # If white noise is playing, lower its volume
            if self.is_white_noise_playing():
                logger.debug("Lowering white noise volume for alarm")
                self._adjust_white_noise_volume(20)  # Lower to 20% or another appropriate value
            
            # Randomly select an alarm sound from the loaded sounds
            selected_alarm_key = random.choice(alarm_sounds)
            
            # Get channel and prepare outside lock
            channel = pygame.mixer.find_channel()
            if not channel:
                logger.warning("No available channel to play alarm")
                return
                
            # Set volume and play (these are fast operations)
            channel.set_volume(self._alarm_volume / 100.0)
            channel.play(self._sounds[selected_alarm_key], loops=-1)  # Loop indefinitely
            
            # Update state with lock
            with self._lock:
                self._alarm_channel = channel
                self._alarm_playing = True
                
            logger.info(f"Alarm started playing: {selected_alarm_key}")
            
            # Broadcast alarm status update
            self._broadcast_alarm_status(True)
        except Exception as e:
            logger.error(f"Failed to play alarm: {str(e)}")

    def stop_alarm(self) -> None:
        """Stop the currently playing alarm and restore white noise volume if needed."""
        # Handle mock mode with minimal locking
        if self._mock_mode:
            with self._lock:
                self._alarm_playing = False
                logger.info("Mock mode: Alarm stopped")
            # Broadcast alarm status update
            self._broadcast_alarm_status(False)
            return
        
        # Get current state with minimal locking
        channel = None
        was_playing = False
        restore_white_noise = False
        previous_volume = 0
        
        with self._lock:
            channel = self._alarm_channel
            was_playing = channel is not None and channel.get_busy()
            restore_white_noise = self._white_noise_playing and was_playing
            previous_volume = self._previous_volume
            
            if not was_playing:
                # Nothing to stop, just update state
                self._alarm_playing = False
                return
        
        # Perform the stop operation outside the lock
        try:
            # Stop the channel (fast operation)
            channel.stop()
            
            # Update state with lock
            with self._lock:
                self._alarm_playing = False
            
            # Restore white noise volume if it was playing
            if restore_white_noise:
                logger.debug(f"Restoring white noise volume to {previous_volume}%")
                self._adjust_white_noise_volume(previous_volume)
                
            logger.info("Alarm stopped")
            
            # Broadcast alarm status update
            self._broadcast_alarm_status(False)
        except Exception as e:
            logger.error(f"Failed to stop alarm: {str(e)}")

    def play_white_noise(self) -> bool:
        """
        Play white noise sound.
        
        Returns:
            bool: True if operation was successful, False otherwise
        """
        # Handle mock mode with minimal locking
        if self._mock_mode:
            with self._lock:
                self._white_noise_playing = True
                logger.info("Mock mode: White noise started playing")
            # Broadcast white noise status update
            self._broadcast_white_noise_status(True)
            return True
        
        # Get current state with minimal locking
        channel = None
        with self._lock:
            channel = self._white_noise_channel
            if not channel or not channel.get_busy():
                # Nothing to stop, just update state
                self._white_noise_playing = False
                return True
            
        # Validate sound is loaded (quick check first)
        if 'white_noise' not in self._sounds:
            logger.error("White noise sound not loaded - cannot play")
            with self._lock:
                self._white_noise_playing = False
            return False
            
        # Check if sound is valid
        if not self._sounds['white_noise']:
            logger.error("White noise sound is invalid - cannot play")
            with self._lock:
                self._white_noise_playing = False
            return False
            
        # Main playback with minimal locked sections
        try:
            # Stop any current playback (handles its own locking)
            self.stop_white_noise()
            
            # Get channel and prepare outside lock
            channel = pygame.mixer.find_channel()
            if not channel:
                logger.error("No available channel to play white noise - all channels in use")
                with self._lock:
                    self._white_noise_playing = False
                return False
            
            # Determine appropriate volume based on alarm state
            volume = self._volume
            alarm_is_playing = self.is_alarm_playing()
            
            # If alarm is playing, use reduced volume
            if alarm_is_playing:
                volume = min(volume, 20)  # Cap at 20% when alarm is playing
                logger.debug(f"Alarm is playing, using reduced white noise volume: {volume}%")
            
            # Set volume and play (these are fast operations)
            channel.set_volume(volume / 100.0)
            channel.play(self._sounds['white_noise'], loops=-1)  # Loop indefinitely
            
            # Final state update with lock
            with self._lock:
                self._white_noise_channel = channel
                self._white_noise_playing = True
                self._previous_volume = self._volume  # Store for restoration
                
            logger.info("White noise started playing")
            
            # Broadcast white noise status update
            self._broadcast_white_noise_status(True)
            return True
            
        except pygame.error as e:
            logger.error(f"Pygame error playing white noise: {str(e)}")
            with self._lock:
                self._white_noise_playing = False
            return False
        except Exception as e:
            logger.error(f"Failed to play white noise: {str(e)}")
            with self._lock:
                self._white_noise_playing = False
            return False

    def stop_white_noise(self) -> bool:
        """
        Stop the currently playing white noise.
        
        Returns:
            bool: True if white noise was stopped successfully, False otherwise
        """
        # Handle mock mode with minimal locking
        if self._mock_mode:
            with self._lock:
                self._white_noise_playing = False
                logger.info("Mock mode: White noise stopped")
            # Broadcast white noise status update
            self._broadcast_white_noise_status(False)
            return True
        
        # Get current state with minimal locking
        channel = None
        with self._lock:
            channel = self._white_noise_channel
            if not channel or not channel.get_busy():
                # Nothing to stop, just update state
                self._white_noise_playing = False
                return True
        
        # Perform the stop operation outside the lock
        try:
            # Stop the channel (fast operation)
            channel.stop()
            
            # Update state with lock
            with self._lock:
                self._white_noise_playing = False
                
            logger.info("White noise stopped")
            
            # Broadcast white noise status update
            self._broadcast_white_noise_status(False)
            return True
        except pygame.error as e:
            logger.error(f"Pygame error stopping white noise: {str(e)}")
            with self._lock:
                self._white_noise_playing = False
            return False
        except Exception as e:
            logger.error(f"Failed to stop white noise: {str(e)}")
            with self._lock:
                self._white_noise_playing = False
            return False

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
        # Validate volume range before acquiring any locks
        if not 0 <= volume <= 100:
            raise ValueError("Volume must be between 0 and 100")
        
        # Update internal volume state with minimal locking
        with self._lock:
            self._volume = volume
            self._previous_volume = volume  # Update for restoration purposes
        
        # Apply volume to white noise channel if active
        if not self._mock_mode and self.is_white_noise_playing():
            try:
                # Apply appropriate volume based on alarm state
                effective_volume = min(volume, 20) if self.is_alarm_playing() else volume
                self._white_noise_channel.set_volume(effective_volume / 100.0)
            except Exception as e:
                logger.error(f"Error setting white noise volume: {e}")
        
        # Save to settings (outside lock)
        if self._settings_manager is not None:
            try:
                self._settings_manager.set_volume(volume)
            except Exception as e:
                logger.warning(f"Failed to save volume to settings: {e}")
                
        logger.info(f"Volume adjusted to {volume}%")
        
        # Broadcast volume update
        self._broadcast_volume_update(volume)
        
    def _adjust_white_noise_volume(self, volume: int) -> None:
        """
        Internal method to adjust only the white noise volume temporarily.
        This is used when an alarm is playing to reduce white noise volume
        without affecting the stored volume setting.
        
        Args:
            volume: Volume level (0-100)
        """
        # Validate volume range
        volume = max(0, min(100, volume))
        
        # Apply to white noise channel if active
        if not self._mock_mode and self.is_white_noise_playing() and self._white_noise_channel:
            try:
                self._white_noise_channel.set_volume(volume / 100.0)
                logger.debug(f"White noise volume temporarily adjusted to {volume}%")
            except Exception as e:
                logger.error(f"Error setting white noise volume: {e}")

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
            
            # First check our state variable for quick return
            if not self._white_noise_playing:
                return False
                
            # Verify with the actual channel state
            channel_playing = (self._white_noise_channel is not None and 
                              self._white_noise_channel.get_busy())
            
            # Update state if there's a mismatch
            if not channel_playing:
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
        # No need for lock here as the called methods handle their own locking
        if self.is_white_noise_playing():
            return self.stop_white_noise()
        else:
            return self.play_white_noise()
    
    def get_volume(self) -> int:
        """Get the current master volume level."""
        with self._lock:
            return self._volume
            
    def get_white_noise_volume(self) -> int:
        """Get the current white noise volume level."""
        with self._lock:
            # If alarm is playing, white noise is at reduced volume
            if self.is_alarm_playing() and self.is_white_noise_playing():
                return min(self._volume, 20)
            return self._volume
            
    def get_alarm_volume(self) -> int:
        """Get the current alarm volume level."""
        with self._lock:
            return self._alarm_volume
            
    def set_alarm_volume(self, volume: int) -> None:
        """Set the alarm volume level."""
        # Validate volume range
        if not 0 <= volume <= 100:
            raise ValueError("Volume must be between 0 and 100")
            
        with self._lock:
            self._alarm_volume = volume
            
        # Apply to alarm channel if active (outside lock)
        if not self._mock_mode and self.is_alarm_playing() and self._alarm_channel:
            try:
                self._alarm_channel.set_volume(volume / 100.0)
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
        if self._mock_mode:
            with self._lock:
                self._alarm_playing = False
                self._white_noise_playing = False
            logger.info("Mock mode: Audio resources cleaned up")
            return
            
        try:
            # Stop any playing sounds
            if self.is_alarm_playing():
                self.stop_alarm()
            if self.is_white_noise_playing():
                self.stop_white_noise()
                
            # Quit pygame mixer if initialized
            if not self._mock_mode and pygame.mixer.get_init():
                pygame.mixer.quit()
                logger.info("Pygame mixer closed")
                
            logger.info("Audio resources cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during audio cleanup: {str(e)}")
            
    def _broadcast_alarm_status(self, is_playing: bool) -> None:
        """Broadcast alarm status update via WebSocket."""
        try:
            # Import here to avoid circular imports
            from backend.websocket_manager import connection_manager
            
            # Run the broadcast in a background task to avoid blocking
            asyncio.create_task(connection_manager.broadcast_alarm_status(is_playing))
        except Exception as e:
            logger.error(f"Failed to broadcast alarm status update: {e}")
    
    def _broadcast_white_noise_status(self, is_playing: bool) -> None:
        """Broadcast white noise status update via WebSocket."""
        try:
            # Import here to avoid circular imports
            from backend.websocket_manager import connection_manager
            
            # Run the broadcast in a background task to avoid blocking
            asyncio.create_task(connection_manager.broadcast_white_noise_status(is_playing))
        except Exception as e:
            logger.error(f"Failed to broadcast white noise status update: {e}")
    
    def _broadcast_volume_update(self, volume: int) -> None:
        """Broadcast volume update via WebSocket."""
        try:
            # Import here to avoid circular imports
            from backend.websocket_manager import connection_manager
            
            # Run the broadcast in a background task to avoid blocking
            asyncio.create_task(connection_manager.broadcast_volume_update(volume))
        except Exception as e:
            logger.error(f"Failed to broadcast volume update: {e}")
