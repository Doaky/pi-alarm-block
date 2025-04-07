"""Schedule-related route handlers."""

import logging
from fastapi import APIRouter, Depends
from typing import Dict, Any

from backend.settings_manager import SettingsManager
from backend.utils.error_handler import ValidationError, AlarmBlockError
from backend.dependencies import get_settings_manager
from backend.websocket_manager import connection_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/schedule")
async def get_schedule(
    settings_manager: SettingsManager = Depends(get_settings_manager)
):
    """Gets the current schedule settings."""
    try:
        # Return the schedule in the format expected by the frontend: { schedule: "a" | "b" | "off" }
        schedule = settings_manager.get_schedule()
        return {"schedule": schedule}
    except Exception as e:
        logger.error(f"Error fetching schedule: {str(e)}")
        raise AlarmBlockError("Failed to fetch schedule")

@router.put("/schedule")
async def set_schedule(
    schedule: Dict[str, Any],
    settings_manager: SettingsManager = Depends(get_settings_manager)
):
    """Updates the schedule settings."""
    try:
        if "schedule" not in schedule:
            raise ValidationError("Missing schedule data")
        
        # Update the schedule in settings manager
        settings_manager.set_schedule(schedule["schedule"])
        logger.info("Schedule updated successfully")
        
        # Broadcast the schedule update to all connected clients
        # Use the schedule string directly
        await connection_manager.broadcast_schedule_update(schedule["schedule"])
        
        return {"message": "Schedule updated successfully", "schedule": schedule["schedule"]}
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error updating schedule: {str(e)}")
        raise AlarmBlockError("Failed to update schedule")
