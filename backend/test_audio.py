#!/usr/bin/env python3
"""
Audio System Test Script for Raspberry Pi

This script tests the audio playback functionality on the Raspberry Pi,
focusing on white noise and alarm sounds. It helps diagnose issues with
the pygame mixer and sound file loading.

Usage:
    python test_audio.py [--test-type=TYPE]

Options:
    --test-type=TYPE    Type of test to run (default: all)
                        Valid values: all, init, white_noise, alarm, files
"""

import os
import sys
import time
import logging
import argparse
import pygame
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('audio_test')

def setup_test_environment():
    """Set up the test environment and return the paths to sound files."""
    # Get the project root directory
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    project_root = script_dir.parent
    
    # Define paths
    sounds_dir = project_root / "backend" / "data" / "sounds"
    alarm_sounds_dir = sounds_dir / "alarms"
    white_noise_path = sounds_dir / "white_noise.ogg"
    
    # Ensure directories exist
    sounds_dir.mkdir(parents=True, exist_ok=True)
    alarm_sounds_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Sounds directory: {sounds_dir}")
    logger.info(f"Alarm sounds directory: {alarm_sounds_dir}")
    logger.info(f"White noise path: {white_noise_path}")
    
    return {
        'project_root': project_root,
        'sounds_dir': sounds_dir,
        'alarm_sounds_dir': alarm_sounds_dir,
        'white_noise_path': white_noise_path
    }

def test_pygame_initialization():
    """Test pygame and mixer initialization."""
    logger.info("Testing pygame initialization...")
    
    try:
        # First, try to initialize pygame
        pygame.init()
        logger.info(f"Pygame initialized: {pygame.get_init()}")
        
        # Check available audio drivers
        logger.info(f"Available audio drivers: {pygame.mixer.get_sdl_mixer_version()}")
        
        # Try different audio drivers
        drivers_to_try = ['alsa', 'pulseaudio', 'dummy']
        
        for driver in drivers_to_try:
            try:
                logger.info(f"Trying audio driver: {driver}")
                os.environ['SDL_AUDIODRIVER'] = driver
                
                # Try to initialize the mixer with different settings
                pygame.mixer.quit()  # Ensure mixer is not already initialized
                
                # Try with default settings first
                pygame.mixer.init()
                logger.info(f"Mixer initialized with default settings using {driver}")
                logger.info(f"Mixer settings: {pygame.mixer.get_init()}")
                pygame.mixer.quit()
                
                # Try with specific settings for Raspberry Pi
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
                logger.info(f"Mixer initialized with custom settings using {driver}")
                logger.info(f"Mixer settings: {pygame.mixer.get_init()}")
                
                # If we got here, the initialization worked
                logger.info(f"Successfully initialized mixer with {driver} driver")
                break
                
            except Exception as e:
                logger.error(f"Failed to initialize mixer with {driver} driver: {e}")
                continue
        
        # Check if mixer is initialized
        if pygame.mixer.get_init():
            logger.info("Mixer is initialized")
            logger.info(f"Mixer settings: {pygame.mixer.get_init()}")
            logger.info(f"Number of channels: {pygame.mixer.get_num_channels()}")
            return True
        else:
            logger.error("Failed to initialize mixer with any driver")
            return False
            
    except Exception as e:
        logger.error(f"Error during pygame initialization: {e}")
        return False

def test_sound_files(paths):
    """Test sound file loading and properties."""
    logger.info("Testing sound files...")
    
    # Check if white noise file exists
    if not os.path.exists(paths['white_noise_path']):
        logger.error(f"White noise file not found: {paths['white_noise_path']}")
    else:
        logger.info(f"White noise file exists: {paths['white_noise_path']}")
        logger.info(f"File size: {os.path.getsize(paths['white_noise_path'])} bytes")
        
    # Check alarm sounds directory
    alarm_files = list(paths['alarm_sounds_dir'].glob('*.ogg'))
    logger.info(f"Found {len(alarm_files)} alarm sound files")
    
    for alarm_file in alarm_files:
        logger.info(f"Alarm file: {alarm_file}")
        logger.info(f"File size: {os.path.getsize(alarm_file)} bytes")
    
    # Try to load each sound file with pygame
    if pygame.mixer.get_init():
        try:
            # Try to load white noise
            if os.path.exists(paths['white_noise_path']):
                try:
                    white_noise = pygame.mixer.Sound(str(paths['white_noise_path']))
                    logger.info(f"Successfully loaded white noise sound")
                    logger.info(f"White noise length: {white_noise.get_length()} seconds")
                except Exception as e:
                    logger.error(f"Failed to load white noise sound: {e}")
            
            # Try to load alarm sounds
            for alarm_file in alarm_files:
                try:
                    alarm_sound = pygame.mixer.Sound(str(alarm_file))
                    logger.info(f"Successfully loaded alarm sound: {alarm_file}")
                    logger.info(f"Alarm sound length: {alarm_sound.get_length()} seconds")
                except Exception as e:
                    logger.error(f"Failed to load alarm sound {alarm_file}: {e}")
                    
            return True
        except Exception as e:
            logger.error(f"Error testing sound files: {e}")
            return False
    else:
        logger.error("Mixer not initialized, cannot test sound files")
        return False

def test_white_noise_playback():
    """Test white noise playback."""
    logger.info("Testing white noise playback...")
    
    if not pygame.mixer.get_init():
        logger.error("Mixer not initialized, cannot test white noise playback")
        return False
        
    try:
        # Get paths
        paths = setup_test_environment()
        
        # Check if white noise file exists
        if not os.path.exists(paths['white_noise_path']):
            logger.error(f"White noise file not found: {paths['white_noise_path']}")
            return False
            
        # Load white noise sound
        try:
            white_noise = pygame.mixer.Sound(str(paths['white_noise_path']))
            logger.info(f"Successfully loaded white noise sound")
        except Exception as e:
            logger.error(f"Failed to load white noise sound: {e}")
            return False
            
        # Find a channel to play on
        channel = pygame.mixer.find_channel()
        if not channel:
            logger.error("No available channel to play white noise")
            return False
            
        # Set volume and play
        channel.set_volume(0.5)  # 50% volume
        channel.play(white_noise, loops=0)  # Play once
        
        logger.info("White noise started playing")
        logger.info("Waiting 3 seconds...")
        time.sleep(3)
        
        # Check if still playing
        if channel.get_busy():
            logger.info("White noise is still playing after 3 seconds")
            channel.stop()
            logger.info("White noise stopped")
            return True
        else:
            logger.error("White noise stopped playing before 3 seconds")
            return False
            
    except Exception as e:
        logger.error(f"Error testing white noise playback: {e}")
        return False

def test_alarm_playback():
    """Test alarm sound playback."""
    logger.info("Testing alarm sound playback...")
    
    if not pygame.mixer.get_init():
        logger.error("Mixer not initialized, cannot test alarm playback")
        return False
        
    try:
        # Get paths
        paths = setup_test_environment()
        
        # Check alarm sounds directory
        alarm_files = list(paths['alarm_sounds_dir'].glob('*.ogg'))
        if not alarm_files:
            logger.error(f"No alarm sound files found in {paths['alarm_sounds_dir']}")
            return False
            
        # Load first alarm sound
        try:
            alarm_sound = pygame.mixer.Sound(str(alarm_files[0]))
            logger.info(f"Successfully loaded alarm sound: {alarm_files[0]}")
        except Exception as e:
            logger.error(f"Failed to load alarm sound: {e}")
            return False
            
        # Find a channel to play on
        channel = pygame.mixer.find_channel()
        if not channel:
            logger.error("No available channel to play alarm")
            return False
            
        # Set volume and play
        channel.set_volume(0.7)  # 70% volume
        channel.play(alarm_sound, loops=0)  # Play once
        
        logger.info("Alarm started playing")
        logger.info("Waiting 3 seconds...")
        time.sleep(3)
        
        # Check if still playing
        if channel.get_busy():
            logger.info("Alarm is still playing after 3 seconds")
            channel.stop()
            logger.info("Alarm stopped")
            return True
        else:
            logger.error("Alarm stopped playing before 3 seconds")
            return False
            
    except Exception as e:
        logger.error(f"Error testing alarm playback: {e}")
        return False

def cleanup():
    """Clean up resources."""
    logger.info("Cleaning up resources...")
    
    try:
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        pygame.quit()
        logger.info("Pygame resources cleaned up")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def main():
    """Main function to run tests."""
    parser = argparse.ArgumentParser(description='Test audio playback on Raspberry Pi')
    parser.add_argument('--test-type', type=str, default='all',
                        help='Type of test to run (all, init, white_noise, alarm, files)')
    
    args = parser.parse_args()
    test_type = args.test_type.lower()
    
    logger.info(f"Starting audio test with test type: {test_type}")
    
    try:
        # Setup test environment
        paths = setup_test_environment()
        
        # Run tests based on test type
        if test_type in ['all', 'init']:
            test_pygame_initialization()
            
        if test_type in ['all', 'files']:
            test_sound_files(paths)
            
        if test_type in ['all', 'white_noise']:
            test_white_noise_playback()
            
        if test_type in ['all', 'alarm']:
            test_alarm_playback()
            
    except Exception as e:
        logger.error(f"Error during tests: {e}")
    finally:
        cleanup()
        
    logger.info("Audio tests completed")

if __name__ == "__main__":
    main()
