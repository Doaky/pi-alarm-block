"""Audio control route handlers."""

import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.utils.error_handler import ValidationError, AlarmBlockError
from backend.dependencies import get_audio_manager
from backend.dependencies import AudioManager
from backend.config import USE_PI_HARDWARE
from backend.websocket_manager import connection_manager

logger = logging.getLogger(__name__)
# Define the router with explicit tags for OpenAPI documentation
router = APIRouter(tags=["audio"])

class WhiteNoiseAction(BaseModel):
    """Model for white noise control actions."""
    action: str = Field(..., description="Action to perform: 'play' or 'stop'")

class VolumeControl(BaseModel):
    """Model for volume control."""
    volume: int = Field(..., ge=0, le=100, description="Volume level (0-100)")

@router.post("/play-alarm", 
    summary="Play alarm sound",
    description="Plays the alarm sound through the audio system",
    response_description="Message indicating the alarm is playing",
    responses={
        200: {"description": "Alarm started playing successfully"},
        500: {"description": "Failed to play alarm"}
    }
)
async def play_alarm(
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
        # Always use audio_manager for playing alarms
        audio_manager.play_alarm()
        
        # Broadcast alarm status update to all connected clients
        await connection_manager.broadcast_alarm_status(True)
        
        if not USE_PI_HARDWARE:
            logger.info("Alarm playing (development mode)")
            return {"message": "Alarm playing (development mode)"}
        else:
            logger.info("Alarm playing")
            return {"message": "Alarm playing"}
    except Exception as e:
        logger.error(f"Error playing alarm: {str(e)}")
        raise AlarmBlockError("Failed to play alarm")

@router.post("/stop-alarm", 
    summary="Stop alarm sound",
    description="Stops the currently playing alarm sound",
    response_description="Message indicating the alarm is stopped",
    responses={
        200: {"description": "Alarm stopped successfully"},
        500: {"description": "Failed to stop alarm"}
    }
)
async def stop_alarm(
    audio_manager: AudioManager = Depends(get_audio_manager)
):
    """
    Stops the currently playing alarm sound.
    
    - In hardware mode: Uses the Raspberry Pi hardware
    - In development mode: Uses the audio manager
    
    Returns:
        dict: Message indicating the alarm is stopped
    """
    try:
        # Always use audio_manager for stopping alarms
        audio_manager.stop_alarm()
        
        # Broadcast alarm status update to all connected clients
        await connection_manager.broadcast_alarm_status(False)
        
        if not USE_PI_HARDWARE:
            logger.info("Alarm stopped (development mode)")
            return {"message": "Alarm stopped (development mode)"}
        else:
            logger.info("Alarm stopped")
            return {"message": "Alarm stopped"}
    except Exception as e:
        logger.error(f"Error stopping alarm: {str(e)}")
        raise AlarmBlockError("Failed to stop alarm")

@router.post("/white-noise", 
    summary="Control white noise",
    description="Controls white noise playback (play or stop)",
    response_description="Message indicating the white noise status",
    responses={
        200: {"description": "White noise control successful"},
        400: {"description": "Invalid action provided"},
        500: {"description": "Failed to control white noise"}
    }
)
async def white_noise(
    action: WhiteNoiseAction,
    audio_manager: AudioManager = Depends(get_audio_manager)
):
    """
    Controls white noise playback.
    
    - action: "play" to start white noise, "stop" to stop it
    - In hardware mode: Uses the Raspberry Pi hardware
    - In development mode: Uses the audio manager
    
    Returns:
        dict: Message indicating the white noise status
    """
    try:
        # Validate action first
        if action.action not in ["play", "stop"]:
            raise ValidationError(f"Invalid action: {action.action}")
        
        # Handle the action
        if action.action == "play":
            success = audio_manager.play_white_noise()
            status_msg = "playing"
            
            if not success:
                logger.error("Failed to play white noise")
                raise AlarmBlockError("Failed to play white noise")
                
            # Broadcast white noise status update
            await connection_manager.broadcast_white_noise_status(True)
        else:  # action.action == "stop"
            success = audio_manager.stop_white_noise()
            status_msg = "stopped"
            
            if not success:
                logger.error("Failed to stop white noise")
                raise AlarmBlockError("Failed to stop white noise")
                
            # Broadcast white noise status update
            await connection_manager.broadcast_white_noise_status(False)
            
        if not USE_PI_HARDWARE:
            logger.info(f"White noise {status_msg} (development mode)")
            return {"message": f"White noise {status_msg} (development mode)"}
        else:
            logger.info(f"White noise {status_msg}")
            return {"message": f"White noise {status_msg}"}
    except Exception as e:
        logger.error(f"Error controlling white noise: {str(e)}")
        raise AlarmBlockError("Failed to control white noise")

@router.post("/volume", 
    summary="Adjust volume",
    description="Adjusts the system volume level",
    response_description="Message indicating the volume was adjusted",
    responses={
        200: {"description": "Volume adjusted successfully"},
        400: {"description": "Invalid volume level"},
        500: {"description": "Failed to adjust volume"}
    }
)
async def adjust_volume(
    volume_data: VolumeControl,
    audio_manager: AudioManager = Depends(get_audio_manager)
):
    """
    Adjusts the volume.
    
    - volume: Integer value between 0 and 100
    - In hardware mode: Uses the Raspberry Pi hardware
    - In development mode: Uses the audio manager
    
    Returns:
        dict: Message indicating the volume was adjusted
    """
    try:
        volume = volume_data.volume
        if not 0 <= volume <= 100:
            raise ValidationError("Volume must be between 0 and 100")
        
        # Always use audio_manager for volume control
        audio_manager.adjust_volume(volume)
        
        # Broadcast volume update to all connected clients
        await connection_manager.broadcast_volume_update(volume)
        
        if not USE_PI_HARDWARE:
            logger.info(f"Volume set to {volume} (development mode)")
            return {"message": f"Volume set to {volume} (development mode)"}
        else:
            logger.info(f"Volume set to {volume}")
            return {"message": f"Volume set to {volume}"}
    except Exception as e:
        logger.error(f"Error adjusting volume: {str(e)}")
        raise AlarmBlockError("Failed to adjust volume")

@router.get("/white-noise/status", 
    summary="Get white noise status",
    description="Checks if white noise is currently playing",
    response_description="Status of white noise playback",
    responses={
        200: {"description": "Successfully retrieved white noise status"},
        500: {"description": "Failed to get white noise status"}
    }
)

async def get_white_noise_status(
    audio_manager: AudioManager = Depends(get_audio_manager)
):
    """
    Get the current status of white noise playback.
    
    - In hardware mode: Uses the Raspberry Pi hardware
    - In development mode: Uses the audio manager
    
    Returns:
        dict: Status indicating if white noise is playing
    """
    try:
        is_playing = audio_manager.is_white_noise_playing()
        
        if not USE_PI_HARDWARE:
            logger.info(f"White noise status checked: {is_playing} (development mode)")
            return {"is_playing": is_playing, "mode": "development"}
        else:
            logger.info(f"White noise status checked: {is_playing}")
            return {"is_playing": is_playing, "mode": "hardware"}
    except Exception as e:
        logger.error(f"Error checking white noise status: {str(e)}")
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
async def get_volume(
    audio_manager: AudioManager = Depends(get_audio_manager)
):
    """
    Get the current volume level.
    
    - In hardware mode: Uses the Raspberry Pi hardware
    - In development mode: Uses the audio manager
    
    Returns:
        dict: Current volume level (0-100)
    """
    try:
        volume = audio_manager.get_volume()
        
        if not USE_PI_HARDWARE:
            logger.info(f"Volume level checked: {volume} (development mode)")
            return {"volume": volume, "mode": "development"}
        else:
            logger.info(f"Volume level checked: {volume}")
            return {"volume": volume, "mode": "hardware"}
    except Exception as e:
        logger.error(f"Error retrieving volume level: {str(e)}")
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
async def get_alarm_status(
    audio_manager: AudioManager = Depends(get_audio_manager)
):
    """
    Get the current status of alarm playback.
    
    - In hardware mode: Uses the Raspberry Pi hardware
    - In development mode: Uses the audio manager
    
    Returns:
        dict: Status indicating if alarm is playing
    """
    try:
        is_playing = audio_manager.is_alarm_playing()
        
        if not USE_PI_HARDWARE:
            logger.info(f"Alarm status checked: {is_playing} (development mode)")
            return {"is_playing": is_playing, "mode": "development"}
        else:
            logger.info(f"Alarm status checked: {is_playing}")
            return {"is_playing": is_playing, "mode": "hardware"}
    except Exception as e:
        logger.error(f"Error checking alarm status: {str(e)}")
        raise AlarmBlockError("Failed to get alarm status")
