import logging
from typing import Any, Dict, Literal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from backend.dependencies import get_settings_manager
from backend.services.settings_manager import SettingsManager
from backend.services.websocket_manager import web_socket_manager
from backend.utils.error_handler import AlarmBlockError, ValidationError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["schedule"])

class ScheduleResponse(BaseModel):
    """Response model for schedule endpoints."""
    schedule: Literal["a", "b", "off"]
    
class ScheduleUpdateResponse(BaseModel):
    """Response model for schedule update endpoint."""
    message: str
    schedule: Literal["a", "b", "off"]

@router.get(
    "/schedule",
    response_model=ScheduleResponse,
    summary="Get current schedule",
    description="Returns the current active schedule setting",
    responses={
        status.HTTP_200_OK: {"description": "Successfully retrieved schedule"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to fetch schedule"}
    }
)
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

@router.put(
    "/schedule",
    response_model=ScheduleUpdateResponse,
    summary="Update schedule",
    description="Updates the current schedule setting",
    responses={
        status.HTTP_200_OK: {"description": "Schedule updated successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid schedule data"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to update schedule"}
    }
)
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
        await web_socket_manager.broadcast_schedule_update(schedule["schedule"])
        
        return {"message": "Schedule updated successfully", "schedule": schedule["schedule"]}
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error updating schedule: {str(e)}")
        raise AlarmBlockError("Failed to update schedule")
