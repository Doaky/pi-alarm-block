"""Audio control route handlers."""

import logging
from fastapi import APIRouter, Depends
from typing import Optional

from backend.utils.error_handler import HardwareError
from backend.dependencies import get_pi_handler, IS_RASPBERRY_PI
from backend.pi_handler import PiHandler

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/stop-alarm")
async def stop(
    pi_handler: Optional[PiHandler] = Depends(get_pi_handler)
):
    """Stops the currently playing alarm."""
    try:
        if not IS_RASPBERRY_PI:
            return {"message": "No hardware available"}
        pi_handler.stop_alarm()  # type: ignore
        logger.info("Alarm stopped")
        return {"message": "Alarm stopped"}
    except Exception as e:
        logger.error(f"Error stopping alarm: {str(e)}")
        raise HardwareError("Failed to stop alarm")

@router.post("/play-alarm")
async def play(
    pi_handler: Optional[PiHandler] = Depends(get_pi_handler)
):
    """Plays an alarm."""
    try:
        if not IS_RASPBERRY_PI:
            return {"message": "No hardware available"}
        pi_handler.play_alarm()  # type: ignore
        logger.info("Alarm playing")
        return {"message": "Alarm playing"}
    except Exception as e:
        logger.error(f"Error playing alarm: {str(e)}")
        raise HardwareError("Failed to play alarm")

@router.post("/white-noise/play")
async def play_white_noise(
    pi_handler: Optional[PiHandler] = Depends(get_pi_handler)
):
    """Starts playing white noise."""
    try:
        if not IS_RASPBERRY_PI:
            return {"message": "No hardware available"}
        pi_handler.play_white_noise()  # type: ignore
        logger.info("White noise started")
        return {"message": "White noise playing"}
    except Exception as e:
        logger.error(f"Error playing white noise: {str(e)}")
        raise HardwareError("Failed to play white noise")

@router.post("/white-noise/stop")
async def stop_white_noise(
    pi_handler: Optional[PiHandler] = Depends(get_pi_handler)
):
    """Stops playing white noise."""
    try:
        if not IS_RASPBERRY_PI:
            return {"message": "No hardware available"}
        pi_handler.stop_white_noise()  # type: ignore
        logger.info("White noise stopped")
        return {"message": "White noise stopped"}
    except Exception as e:
        logger.error(f"Error stopping white noise: {str(e)}")
        raise HardwareError("Failed to stop white noise")
