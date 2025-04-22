import asyncio
import os
import random
import threading
from typing import Dict, List, Optional

import pygame

from backend.utils.logging import get_logger
from backend.services.websocket_manager import web_socket_manager

# Get logger for this module
logger = get_logger(__name__)

class AlarmAudio:
    """
    Manages alarm audio playback with thread safety.
    
    This class handles playing alarm sounds with proper resource management 
    and thread-safe operations.
    """

    def __init__(self, sounds_dir: str, alarm_sounds_dir: str, sounds: Dict[str, pygame.mixer.Sound], 
                 alarm_volume: int, lock: threading.Lock):
        """
        Initialize AlarmAudio.
        
        Args:
            sounds_dir: Directory containing sound files
            alarm_sounds_dir: Subdirectory containing alarm sound files
            sounds: Dictionary of loaded sounds
            alarm_volume: Initial alarm volume (0-100)
            lock: Thread lock for synchronization
        """
        self._sounds_dir = sounds_dir
        self._alarm_sounds_dir = alarm_sounds_dir
        self._sounds = sounds
        self._alarm_volume = alarm_volume
        self._lock = lock
        
        # Initialize playback state variables
        self._alarm_playing = False
        self._alarm_channel: Optional[pygame.mixer.Channel] = None
        self._alarm_sounds: List[str] = []
        
        # Load alarm sounds
        self._load_alarm_sounds()
    
    def _load_alarm_sounds(self) -> None:
        """
        Load alarm sound files into memory.
        """
        try:
            # Load alarm sounds from the alarm_sounds directory
            alarm_sounds_path = os.path.join(self._sounds_dir, self._alarm_sounds_dir)
            
            # Ensure directory exists
            os.makedirs(alarm_sounds_path, exist_ok=True)
            
            # Check if directory is empty
            if not os.path.exists(alarm_sounds_path) or not os.listdir(alarm_sounds_path):
                logger.warning(f"Alarm sounds directory is empty: {alarm_sounds_path}")
                # Load default alarm sound as fallback
                self._load_default_alarm_sound()
                return
                
            # Get all valid sound files in the alarm_sounds directory
            found_sounds = False
            for filename in os.listdir(alarm_sounds_path):
                # Skip files with .Identifier extension (these are Windows metadata files)
                if filename.endswith('.ogg') and not filename.endswith('.Identifier'):
                    full_path = os.path.join(alarm_sounds_path, filename)
                    sound_key = f"alarm_{filename}"
                    try:
                        self._sounds[sound_key] = pygame.mixer.Sound(full_path)
                        self._alarm_sounds.append(sound_key)
                        logger.info(f"Loaded alarm sound: {full_path}")
                        found_sounds = True
                    except Exception as e:
                        logger.error(f"Failed to load sound {full_path}: {str(e)}")
        
            # Check if we found any alarm sounds
            if not found_sounds:
                logger.warning(f"No alarm sounds found in {alarm_sounds_path}, using default")
                # Load default alarm sound as fallback
                self._load_default_alarm_sound()
            else:
                logger.info(f"Loaded {len(self._alarm_sounds)} alarm sounds")
        except Exception as e:
            logger.error(f"Failed to load alarm sounds: {str(e)}")

    def _load_default_alarm_sound(self) -> None:
        """
        Load the default alarm sound as fallback.
        """
        try:
            default_path = os.path.join(self._sounds_dir, "default_alarm.ogg")
            if os.path.exists(default_path):
                sound_key = "alarm_default"
                self._sounds[sound_key] = pygame.mixer.Sound(default_path)
                self._alarm_sounds.append(sound_key)
                logger.info(f"Loaded default alarm sound: {default_path}")
            else:
                logger.error(f"Default alarm sound not found: {default_path}")
        except Exception as e:
            logger.error(f"Failed to load default alarm sound: {str(e)}")

    def play_alarm(self, white_noise_audio=None) -> bool:
        """
        Play alarm sound.
        
        Args:
            white_noise_audio: Optional WhiteNoiseAudio instance to stop white noise
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        
        # Check if we have any alarm sounds loaded
        alarm_sounds = None
        with self._lock:
            alarm_sounds = self._alarm_sounds.copy() if self._alarm_sounds else []
        
        if not alarm_sounds:
            logger.warning("No alarm sounds loaded")
            return False
        
        try:
            # Stop any currently playing alarm (handles its own locking)
            self.stop_alarm()
            
            # Stop white noise if it's playing
            if white_noise_audio:
                logger.debug("Stopping white noise for alarm")
                white_noise_audio.stop_white_noise()
            
            # Randomly select an alarm sound from the loaded sounds
            selected_alarm_key = random.choice(alarm_sounds)
            
            # Get channel and prepare outside lock
            channel = pygame.mixer.find_channel()
            if not channel:
                logger.warning("No available channel to play alarm")
                return False
                
            # Set volume and play (these are fast operations)
            channel.set_volume(self._alarm_volume / 100.0)
            
            # Check if the sound exists and is valid
            if selected_alarm_key not in self._sounds:
                logger.error(f"Selected alarm sound not found: {selected_alarm_key}")
                return False
                
            # Play the sound with error handling
            try:
                channel.play(self._sounds[selected_alarm_key], loops=-1)  # Loop indefinitely
            except Exception as e:
                logger.error(f"Failed to play alarm sound: {str(e)}")
                return False
            
            # Update state with lock
            with self._lock:
                self._alarm_channel = channel
                self._alarm_playing = True
            
            logger.info(f"Alarm started playing: {selected_alarm_key}")
            
            # Handle asyncio task creation properly
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(web_socket_manager.broadcast_alarm_status(True))
                else:
                    # For non-async contexts, run in a new thread or skip if not critical
                    asyncio.run(web_socket_manager.broadcast_alarm_status(True))
            except RuntimeError as e:
                logger.warning(f"Could not broadcast alarm status update: {e}")
                
            return True
        except Exception as e:
            logger.error(f"Failed to play alarm: {str(e)}")
            return False

    def stop_alarm(self) -> None:
        """
        Stop the currently playing alarm sound.
        """
            
        # Get current state with minimal locking
        channel = None
        was_playing = False
        
        with self._lock:
            channel = self._alarm_channel
            was_playing = self._alarm_playing
            self._alarm_playing = False
            self._alarm_channel = None
            
        # Stop alarm sound if it was playing
        if channel and channel.get_busy():
            try:
                channel.stop()
                logger.info("Alarm stopped")
            except Exception as e:
                logger.error(f"Error stopping alarm: {str(e)}")
                
        # Only broadcast if we actually stopped something
        if was_playing:
            # Handle asyncio task creation properly
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(web_socket_manager.broadcast_alarm_status(False))
                else:
                    # For non-async contexts, run in a new thread or skip if not critical
                    asyncio.run(web_socket_manager.broadcast_alarm_status(False))
            except RuntimeError as e:
                logger.warning(f"Could not broadcast alarm status update: {e}")

    def is_alarm_playing(self) -> bool:
        """Check if an alarm is currently playing."""
        with self._lock:
            return self._alarm_channel is not None and self._alarm_channel.get_busy()

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
        if self.is_alarm_playing() and self._alarm_channel:
            try:
                self._alarm_channel.set_volume(volume / 100.0)
            except Exception as e:
                logger.error(f"Error setting alarm volume: {e}")
                    
        logger.info(f"Alarm volume set to {volume}%")