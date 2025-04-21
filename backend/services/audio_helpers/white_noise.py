import os
import threading
from typing import Dict, Optional

import pygame

from backend.utils.logging import get_logger
from backend.services.websocket_manager import WebSocketManager

# Get logger for this module
logger = get_logger(__name__)

class WhiteNoiseAudio:
    """
    Manages white noise audio playback with thread safety.
    
    This class handles playing white noise sounds with proper resource management 
    and thread-safe operations.
    """

    def __init__(self, sounds_dir: str, white_noise_sound: str, sounds: Dict[str, pygame.mixer.Sound], 
                 volume: int, settings_manager=None, lock: threading.Lock = None):
        """
        Initialize WhiteNoiseAudio.
        
        Args:
            sounds_dir: Directory containing sound files
            white_noise_sound: Filename of the white noise sound
            sounds: Dictionary of loaded sounds
            volume: Initial volume (0-100)
            settings_manager: Optional settings manager for volume persistence
            lock: Thread lock for synchronization
        """
        self._sounds_dir = sounds_dir
        self._white_noise_sound = white_noise_sound
        self._sounds = sounds
        self._volume = volume
        self._settings_manager = settings_manager
        self._lock = lock or threading.Lock()
        
        # Initialize playback state variables
        self._white_noise_playing = False
        self._white_noise_channel: Optional[pygame.mixer.Channel] = None
        self._previous_volume = volume  # For restoring white noise volume after alarm
        
        # Load white noise sound
        self._load_white_noise_sound()
    
    def _load_white_noise_sound(self) -> None:
        """
        Load white noise sound file into memory.
        """
        try:
            # Load white noise sound
            white_noise_path = os.path.join(self._sounds_dir, self._white_noise_sound)
            if os.path.exists(white_noise_path):
                try:
                    self._sounds['white_noise'] = pygame.mixer.Sound(white_noise_path)
                    logger.info(f"Loaded white noise sound: {white_noise_path}")
                except Exception as e:
                    logger.error(f"Failed to load white noise sound {white_noise_path}: {str(e)}")
            else:
                logger.warning(f"White noise sound file not found: {white_noise_path}")
        except Exception as e:
            logger.error(f"Failed to load white noise sound: {str(e)}")

    def play_white_noise(self, is_alarm_playing_callback=None) -> bool:
        """
        Play white noise sound.
        
        Args:
            is_alarm_playing_callback: Optional callback to check if alarm is playing
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        
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
            alarm_is_playing = is_alarm_playing_callback() if is_alarm_playing_callback else False
            
            # If alarm is playing, use reduced volume
            if alarm_is_playing:
                volume = min(volume, 0)  # mute when alarm is playing
                logger.debug(f"Alarm is playing, muting white noise")
            
            # Set volume and play (these are fast operations)
            channel.set_volume(volume / 100.0)
            
            # Play the sound with error handling
            try:
                channel.play(self._sounds['white_noise'], loops=-1)  # Loop indefinitely
            except Exception as e:
                logger.error(f"Failed to play white noise sound: {str(e)}")
                with self._lock:
                    self._white_noise_playing = False
                return False
            
            # Final state update with lock
            with self._lock:
                self._white_noise_channel = channel
                self._white_noise_playing = True
                self._previous_volume = self._volume  # Store for restoration
                
            logger.info("White noise started playing")
            
            # Broadcast white noise status update
            WebSocketManager.broadcast_white_noise_status(True)
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

    def stop_white_noise(self) -> None:
        """
        Stop the currently playing white noise sound.
        """
            
        # Get current state with minimal locking
        channel = None
        was_playing = False
        
        with self._lock:
            channel = self._white_noise_channel
            was_playing = self._white_noise_playing
            self._white_noise_playing = False
            self._white_noise_channel = None
            
        # Stop white noise sound if it was playing
        if channel and channel.get_busy():
            try:
                channel.stop()
                logger.info("White noise stopped")
            except Exception as e:
                logger.error(f"Error stopping white noise: {str(e)}")
                
        # Only broadcast if we actually stopped something
        if was_playing:
            # Broadcast white noise status update
            WebSocketManager.broadcast_white_noise_status(False)

    def adjust_volume(self, volume: int) -> None:
        """
        Adjust the master volume level for white noise.
        The master volume is saved to settings and affects white noise only.
        
        Args:
            volume: Volume level (0-100)
        
        Raises:
            ValueError: If volume is outside the valid range
        """
        # Validate volume range
        if not 0 <= volume <= 100:
            raise ValueError("Volume must be between 0 and 100")
            
        # Update volume with lock
        with self._lock:
            self._volume = volume
            self._previous_volume = volume  # Update previous volume too
            
        # Apply to white noise channel if active (outside lock)
        if self.is_white_noise_playing() and self._white_noise_channel:
            try:
                # If alarm is playing, use reduced volume
                applied_volume = volume
                self._white_noise_channel.set_volume(applied_volume / 100.0)
            except Exception as e:
                logger.error(f"Error setting white noise volume: {e}")
                
        # Save to settings if available
        if self._settings_manager is not None:
            try:
                self._settings_manager.set_volume(volume)
            except Exception as e:
                logger.error(f"Error saving volume to settings: {e}")
                
        logger.info(f"Volume set to {volume}%")
        
        WebSocketManager.broadcast_volume_update(volume)
    
    def is_white_noise_playing(self) -> bool:
        """
        Check if white noise is currently playing.
        """
        with self._lock:
            # Check if pygame is initialized
            if not pygame.mixer.get_init():
                return False
                
            # First check our internal state
            if not self._white_noise_playing or self._white_noise_channel is None:
                return False
                
            # Then verify with pygame
            try:
                return self._white_noise_channel.get_busy()
            except Exception as e:
                logger.error(f"Error checking white noise status: {e}")
                # Reset our internal state if there was an error
                self._white_noise_playing = False
                return False

    def toggle_white_noise(self, is_alarm_playing_callback=None) -> bool:
        """
        Toggle white noise on/off.
        
        If white noise is playing, stop it. If not, start playing it.
        
        Args:
            is_alarm_playing_callback: Optional callback to check if alarm is playing
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        if self.is_white_noise_playing():
            return self.stop_white_noise()
        else:
            return self.play_white_noise(is_alarm_playing_callback)

    def get_volume(self) -> int:
        """
        Get the current master volume level.
        """
        with self._lock:
            return self._volume

    def get_white_noise_volume(self) -> int:
        """
        Get the current white noise volume level.
        """
        if self.is_white_noise_playing() and self._white_noise_channel:
            try:
                return int(self._white_noise_channel.get_volume() * 100)
            except Exception:
                pass
        return self.get_volume()
    
    def get_previous_volume(self) -> int:
        """
        Get the previous volume level (for restoring after alarm).
        """
        with self._lock:
            return self._previous_volume