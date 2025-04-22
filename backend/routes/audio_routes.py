"""Audio control route handlers."""

from enum import Enum

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from backend.config import USE_PI_HARDWARE
from backend.dependencies import get_audio_manager
from backend.services.audio_manager import AudioManager
from backend.utils.error_handler import ValidationError, AlarmBlockError
from backend.utils.logging import get_logger

# Get module logger
logger = get_logger(__name__)
# Define the router with explicit tags for OpenAPI documentation
router = APIRouter(tags=["audio"])

class NoiseAction(str, Enum):
    """Possible actions for white noise control."""
    PLAY = "play"
    STOP = "stop"

class WhiteNoiseAction(BaseModel):
    """Model for white noise control actions."""
    action: NoiseAction = Field(..., description="Action to perform: 'play' or 'stop'")

class AudioResponse(BaseModel):
    """Standard response for audio operations."""
    message: str
    status: str = "success"

class VolumeControl(BaseModel):
    """Model for volume control."""
    volume: int = Field(..., ge=0, le=100, description="Volume level (0-100)")

@router.post("/play-alarm", 
    summary="Play alarm sound",
    description="Plays the alarm sound through the audio system",
    response_description="Message indicating the alarm is playing",
    response_model=AudioResponse,
    responses={
        status.HTTP_200_OK: {"description": "Alarm started playing successfully"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to play alarm"}
    }
)
def play_alarm(
    audio_manager: AudioManager = Depends(get_audio_manager)
):
    """
    Plays the alarm sound.
    
    - In hardware mode: Uses the Raspberry Pi hardware
    - In development mode: Uses the audio manager
    
    Returns:
        dict: Message indicating the alarm is playing
    """
    try:
        # AudioManager handles the actual playback and error handling
        audio_manager.play_alarm()
        
        # Determine mode for logging and response
        mode = "development" if not USE_PI_HARDWARE else "hardware"
        message = f"Alarm playing{' (development mode)' if not USE_PI_HARDWARE else ''}"
        
        # Log with structured context
        logger.info("Alarm playing", extra={
            "mode": mode,
            "action": "play_alarm"
        })
        
        # Return standardized response
        return AudioResponse(message=message)
    except Exception as e:
        logger.error(f"Error playing alarm: {e}")
        raise AlarmBlockError("Failed to play alarm")

@router.post("/stop-alarm", 
    summary="Stop alarm sound",
    description="Stops the currently playing alarm sound",
    response_description="Message indicating the alarm has stopped",
    response_model=AudioResponse,
    responses={
        status.HTTP_200_OK: {"description": "Alarm stopped successfully"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to stop alarm"}
    }
)
def stop_alarm(
    audio_manager: AudioManager = Depends(get_audio_manager)
):
    """
    Stops the currently playing alarm sound.
    
    - In hardware mode: Uses the Raspberry Pi hardware
    - In development mode: Uses the audio manager
    
    Returns:
        AudioResponse: Message indicating the alarm has stopped
    """
    try:
        # AudioManager handles the actual stopping and error handling
        audio_manager.stop_alarm()
        
        # Determine mode for logging and response
        mode = "development" if not USE_PI_HARDWARE else "hardware"
        message = f"Alarm stopped{' (development mode)' if not USE_PI_HARDWARE else ''}"
        
        # Log with structured context
        logger.info("Alarm stopped", extra={
            "mode": mode,
            "action": "stop_alarm"
        })
        
        # Return standardized response
        return AudioResponse(message=message)
    except Exception as e:
        logger.error(f"Error stopping alarm: {e}")
        raise AlarmBlockError("Failed to stop alarm")

@router.post("/white-noise", 
    summary="Control white noise",
    description="Start or stop white noise playback",
    response_description="Message indicating the white noise status",
    response_model=AudioResponse,
    responses={
        status.HTTP_200_OK: {"description": "White noise command executed successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid action"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to control white noise"}
    }
)
def white_noise(
    action: WhiteNoiseAction,
    audio_manager: AudioManager = Depends(get_audio_manager)
):
    """
    Controls white noise playback.
    
    - action.action = NoiseAction.PLAY: Start white noise
    - action.action = NoiseAction.STOP: Stop white noise
    
    Returns:
        AudioResponse: Message indicating the white noise status
    """
    try:
        # Let AudioManager handle the action based on the enum
        if action.action == NoiseAction.PLAY:
            success = audio_manager.play_white_noise()
            status_msg = "playing"
            
            if not success:
                raise AlarmBlockError("Failed to play white noise")
        else:  # action.action == NoiseAction.STOP
            success = audio_manager.stop_white_noise()
            status_msg = "stopped"
            
            if not success:
                raise AlarmBlockError("Failed to stop white noise")
                
        # Determine mode for logging and response
        mode = "development" if not USE_PI_HARDWARE else "hardware"
        message = f"White noise {status_msg}{' (development mode)' if not USE_PI_HARDWARE else ''}"
        
        # Log with structured context
        logger.info(f"White noise {status_msg}", extra={
            "mode": mode,
            "action": f"white_noise_{action.action.value}"
        })
        
        # Return standardized response
        return AudioResponse(message=message)
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error controlling white noise: {e}")
        raise AlarmBlockError("Failed to control white noise")

@router.post("/volume", 
    summary="Set volume",
    description="Set the volume level for audio playback",
    response_description="Message indicating the volume has been set",
    response_model=AudioResponse,
    responses={
        status.HTTP_200_OK: {"description": "Volume set successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid volume level"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to set volume"}
    }
)
def set_volume(
    volume_control: VolumeControl,
    audio_manager: AudioManager = Depends(get_audio_manager)
):
    """
    Sets the volume level for audio playback.
    
    - volume_control.volume: Integer between 0-100
    
    Returns:
        AudioResponse: Message indicating the volume has been set
    """
    try:
        # Pydantic handles validation, AudioManager handles the rest
        audio_manager.adjust_volume(volume_control.volume)
        
        # Determine mode for logging and response
        mode = "development" if not USE_PI_HARDWARE else "hardware"
        volume = volume_control.volume
        message = f"Volume set to {volume}{' (development mode)' if not USE_PI_HARDWARE else ''}"
        
        # Log with structured context
        logger.info(f"Volume set to {volume}", extra={
            "mode": mode,
            "action": "set_volume",
            "volume": volume
        })
        
        # Return standardized response
        return AudioResponse(message=message)
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error setting volume: {e}")
        raise AlarmBlockError("Failed to set volume")

@router.get("/white-noise/status", 
    summary="Get white noise status",
    description="Get the current status of white noise playback",
    response_description="Status of white noise playback",
    response_model=AudioResponse,
    responses={
        status.HTTP_200_OK: {"description": "Successfully retrieved white noise status"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to get white noise status"}
    }
)
def get_white_noise_status(
    audio_manager: AudioManager = Depends(get_audio_manager)
):
    """
    Checks if white noise is currently playing.
    
    Returns:
        AudioResponse: Status of white noise playback
    """
    try:
        is_playing = audio_manager.is_white_noise_playing()
        status_text = 'playing' if is_playing else 'stopped'
        
        # Determine mode for logging and response
        mode = "development" if not USE_PI_HARDWARE else "hardware"
        message = f"White noise is {status_text}{' (development mode)' if not USE_PI_HARDWARE else ''}"
        
        # Log with structured context
        logger.info(f"White noise status: {status_text}", extra={
            "mode": mode,
            "action": "get_white_noise_status",
            "is_playing": is_playing
        })
        
        # Return standardized response
        return AudioResponse(
            message=message,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error getting white noise status: {e}")
        raise AlarmBlockError("Failed to get white noise status")

@router.get("/volume", 
    summary="Get current volume",
    description="Retrieves the current system volume level",
    response_description="Current volume level",
    responses={
        200: {"description": "Successfully retrieved volume level"},
        500: {"description": "Failed to get volume level"}
    }
)
def get_volume(
    audio_manager: AudioManager = Depends(get_audio_manager)
):
    """
    Get the current volume level.
    
    Returns:
        dict: Current volume level (0-100)
    """
    try:
        volume = audio_manager.get_volume()
        
        # Determine mode for logging and response
        mode = "development" if not USE_PI_HARDWARE else "hardware"
        
        # Log with structured context
        logger.info(f"Volume level checked: {volume}", extra={
            "mode": mode,
            "action": "get_volume",
            "volume": volume
        })
        
        return {"volume": volume, "mode": mode}
    except Exception as e:
        logger.error(f"Error retrieving volume level: {e}")
        raise AlarmBlockError("Failed to get volume level")

@router.get("/alarm/status", 
    summary="Get alarm status",
    description="Checks if an alarm is currently playing",
    response_description="Status of alarm playback",
    responses={
        200: {"description": "Successfully retrieved alarm status"},
        500: {"description": "Failed to get alarm status"}
    }
)
def get_alarm_status(
    audio_manager: AudioManager = Depends(get_audio_manager)
):
    """
    Get the current status of alarm playback.
    
    Returns:
        dict: Status indicating if alarm is playing
    """
    try:
        is_playing = audio_manager.is_alarm_playing()
        
        # Determine mode for logging and response
        mode = "development" if not USE_PI_HARDWARE else "hardware"
        
        # Log with structured context
        logger.info(f"Alarm status checked: {is_playing}", extra={
            "mode": mode,
            "action": "get_alarm_status",
            "is_playing": is_playing
        })
        
        return {"is_playing": is_playing, "mode": mode}
    except Exception as e:
        logger.error(f"Error checking alarm status: {e}")
        raise AlarmBlockError("Failed to get alarm status")
