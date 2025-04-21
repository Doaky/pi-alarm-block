"""
Mock implementation of AudioManager for development environments.

This module provides a simplified mock implementation of the AudioManager
that can be used in development environments without requiring pygame
or actual audio hardware.
"""

import threading
from typing import Dict, List, Callable

from backend.utils.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)

class MockAudioManager:
    """
    Mock implementation of AudioManager for development environments.
    
    This class mimics the behavior of AudioManager without actually playing
    sounds or requiring audio hardware. It's useful for development and testing.
    """
    
    def __init__(self, settings_manager=None):
        logger.info('MockAudioManager __init__ starting')
        """
        Initialize the MockAudioManager.
        
        Args:
            settings_manager: Optional settings manager for volume persistence
        """
        self._lock = threading.RLock()
        self._settings_manager = settings_manager
        
        # State tracking
        self._initialized = False
        self._white_noise_playing = False
        self._alarm_playing = False
        self._volume = 50  # Default volume (0-100)
        self._alarm_volume = 75  # Default alarm volume (0-100)
        
        # Callback tracking
        self._status_callbacks: List[Callable] = []
        
        logger.info("MockAudioManager initialized")
        self._initialized = True
    
    def initialize(self) -> bool:
        """
        Initialize the audio system.
        
        Returns:
            bool: True if initialization was successful
        """
        with self._lock:
            if self._initialized:
                logger.warning("MockAudioManager already initialized")
                return True
                
            self._initialized = True
            logger.info("MockAudioManager initialized")
            return True
    
    def shutdown(self) -> None:
        """Clean up resources and shut down the audio system."""
        with self._lock:
            self._initialized = False
            self._white_noise_playing = False
            self._alarm_playing = False
            logger.info("MockAudioManager shut down")
    
    def play_alarm(self) -> bool:
        """
        Play alarm sound.
        
        Returns:
            bool: True if operation was successful
        """
        with self._lock:
            self._alarm_playing = True
            logger.info("Mock alarm started playing")
            
        # Broadcast alarm status update
        self._broadcast_alarm_status(True)
        return True
    
    def stop_alarm(self) -> None:
        """Stop the currently playing alarm sound."""
        with self._lock:
            was_playing = self._alarm_playing
            self._alarm_playing = False
            
        if was_playing:
            logger.info("Mock alarm stopped")
            # Broadcast alarm status update
            self._broadcast_alarm_status(False)
    
    def play_white_noise(self) -> bool:
        """
        Play white noise sound.
        Returns:
            bool: True if operation was successful
        """
        with self._lock:
            self._white_noise_playing = True
            logger.info("Mock white noise started playing")
        # Broadcast white noise status update
        self._broadcast_white_noise_status(self._white_noise_playing)
        return True

        """
        Play white noise sound.
        
        Returns:
            bool: True if operation was successful
        """
        with self._lock:
            self._white_noise_playing = True
            logger.info("Mock white noise started playing")
            
        # Broadcast white noise status update
        self._broadcast_white_noise_status(True)
        return True
    
    def stop_white_noise(self) -> None:
        """
        Stop the currently playing white noise sound.
        """
        with self._lock:
            was_playing = self._white_noise_playing
            self._white_noise_playing = False
        if was_playing:
            logger.info("Mock white noise stopped")
            # Broadcast white noise status update
            self._broadcast_white_noise_status(self._white_noise_playing)

        """Stop the currently playing white noise sound."""
        with self._lock:
            was_playing = self._white_noise_playing
            self._white_noise_playing = False
            
        if was_playing:
            logger.info("Mock white noise stopped")
            # Broadcast white noise status update
            self._broadcast_white_noise_status(False)
    
    def adjust_volume(self, volume: int) -> bool:
        """
        Adjust the volume for white noise (alias for set_volume).
        Args:
            volume: Volume level (0-100)
        Returns:
            bool: True if operation was successful
        """
        return self.set_volume(volume)

    def set_volume(self, volume: int) -> bool:
        """
        Set the volume for white noise.
        
        Args:
            volume: Volume level (0-100)
            
        Returns:
            bool: True if operation was successful
        """
        if not 0 <= volume <= 100:
            logger.error(f"Invalid volume level: {volume}")
            return False
            
        with self._lock:
            self._volume = volume
            logger.info(f"Mock white noise volume set to {volume}%")
            
        # Save to settings if available
        if self._settings_manager:
            try:
                if hasattr(self._settings_manager, "set_volume"):
                    self._settings_manager.set_volume(volume)
            except Exception as e:
                logger.error(f"Error saving volume to settings: {str(e)}")
                
        # Broadcast volume status update
        self._broadcast_volume_status(self._volume)
        return True
    
    def set_alarm_volume(self, volume: int) -> bool:
        """
        Set the volume for alarm sounds.
        
        Args:
            volume: Volume level (0-100)
            
        Returns:
            bool: True if operation was successful
        """
        if not 0 <= volume <= 100:
            logger.error(f"Invalid alarm volume level: {volume}")
            return False
            
        with self._lock:
            self._alarm_volume = volume
            logger.info(f"Mock alarm volume set to {volume}%")
            
        # Save to settings if available
        if self._settings_manager:
            try:
                if hasattr(self._settings_manager, "set_alarm_volume"):
                    self._settings_manager.set_alarm_volume(volume)
            except Exception as e:
                logger.error(f"Error saving alarm volume to settings: {str(e)}")
            return True
    
    def get_volume(self) -> int:
        """
        Get the current white noise volume.
        
        Returns:
            int: Current volume (0-100)
        """
        with self._lock:
            return self._volume
    
    def get_alarm_volume(self) -> int:
        """
        Get the current alarm volume.
        
        Returns:
            int: Current alarm volume (0-100)
        """
        with self._lock:
            return self._alarm_volume
    
    def is_white_noise_playing(self) -> bool:
        """
        Check if white noise is currently playing.
        
        Returns:
            bool: True if white noise is playing
        """
        with self._lock:
            return self._white_noise_playing
    
    def is_alarm_playing(self) -> bool:
        """
        Check if alarm is currently playing.
        
        Returns:
            bool: True if alarm is playing
        """
        with self._lock:
            return self._alarm_playing
    
    def register_status_callback(self, callback: Callable) -> None:
        """
        Register a callback for status updates.
        
        Args:
            callback: Function to call with status updates
        """
        with self._lock:
            if callback not in self._status_callbacks:
                self._status_callbacks.append(callback)
                logger.debug(f"Registered status callback: {callback}")
    
    def unregister_status_callback(self, callback: Callable) -> None:
        """
        Unregister a previously registered status callback.
        
        Args:
            callback: Previously registered callback function
        """
        with self._lock:
            if callback in self._status_callbacks:
                self._status_callbacks.remove(callback)
                logger.debug(f"Unregistered status callback: {callback}")
    
    def _broadcast_volume_status(self, volume: int) -> None:
        """
        Broadcast volume status to all registered callbacks.
        Args:
            volume: Current volume level
        """
        status = {"volume": volume}
        self._broadcast_status(status)

    def _broadcast_alarm_volume_status(self, alarm_volume: int) -> None:
        """
        Broadcast alarm volume status to all registered callbacks.
        Args:
            alarm_volume: Current alarm volume level
        """
        status = {"alarm_volume": alarm_volume}
        self._broadcast_status(status)

    def _broadcast_alarm_status(self, is_playing: bool) -> None:
        """
        Broadcast alarm status to all registered callbacks.
        
        Args:
            is_playing: Whether the alarm is playing
        """
        status = {"alarm_playing": is_playing}
        self._broadcast_status(status)
    
    def _broadcast_white_noise_status(self, is_playing: bool) -> None:
        """
        Broadcast white noise status to all registered callbacks.
        
        Args:
            is_playing: Whether white noise is playing
        """
        status = {"white_noise_playing": is_playing}
        self._broadcast_status(status)
    
    def _broadcast_status(self, status: Dict) -> None:
        """
        Broadcast status to all registered callbacks.
        
        Args:
            status: Status dictionary to broadcast
        """
        callbacks = []
        with self._lock:
            callbacks = self._status_callbacks.copy()
            
        for callback in callbacks:
            try:
                callback(status)
            except Exception as e:
                logger.error(f"Error in status callback: {str(e)}")
