"""Audio control route handlers."""

import logging
from fastapi import APIRouter, Depends
from typing import Optional, Dict
from pydantic import BaseModel, Field

from backend.utils.error_handler import HardwareError, ValidationError, AlarmBlockError
from backend.dependencies import get_pi_handler, get_audio_manager
from backend.dependencies import PiHandler, AudioManager
from backend.config import USE_PI_HARDWARE

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
    pi_handler: Optional[PiHandler] = Depends(get_pi_handler),
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
        if not USE_PI_HARDWARE:
            audio_manager.play_alarm()
            return {"message": "Alarm playing (development mode)"}
        if pi_handler is None:
            return {"message": "Hardware interface not available"}
        pi_handler.play_alarm()
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
    pi_handler: Optional[PiHandler] = Depends(get_pi_handler),
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
        if not USE_PI_HARDWARE:
            audio_manager.stop_alarm()
            return {"message": "Alarm stopped (development mode)"}
        if pi_handler is None:
            return {"message": "Hardware interface not available"}
        pi_handler.stop_alarm()
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
    pi_handler: Optional[PiHandler] = Depends(get_pi_handler),
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
        if not USE_PI_HARDWARE:
            if action.action == "play":
                audio_manager.play_white_noise()
                return {"message": "White noise started (development mode)"}
            elif action.action == "stop":
                audio_manager.stop_white_noise()
                return {"message": "White noise stopped (development mode)"}
            else:
                raise ValidationError(f"Invalid action: {action.action}")
        
        if pi_handler is None:
            return {"message": "Hardware interface not available"}
        
        if action.action == "play":
            pi_handler.play_white_noise()
            logger.info("White noise started")
            return {"message": "White noise started"}
        elif action.action == "stop":
            pi_handler.stop_white_noise()
            logger.info("White noise stopped")
            return {"message": "White noise stopped"}
        else:
            raise ValidationError(f"Invalid action: {action.action}")
    except Exception as e:
        logger.error(f"Error controlling white noise: {str(e)}")
        raise HardwareError("Failed to control white noise")

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
    pi_handler: Optional[PiHandler] = Depends(get_pi_handler),
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
        
        if not USE_PI_HARDWARE:
            audio_manager.set_volume(volume)
            return {"message": f"Volume set to {volume} (development mode)"}
        
        if pi_handler is None:
            return {"message": "Hardware interface not available"}
        
        pi_handler.set_volume(volume)
        logger.info(f"Volume set to {volume}")
        return {"message": f"Volume set to {volume}"}
    except Exception as e:
        logger.error(f"Error adjusting volume: {str(e)}")
        raise HardwareError("Failed to adjust volume")
