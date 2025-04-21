"""Alarm-related route handlers."""

from typing import List, Dict, Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from backend.models.alarm import Alarm, AlarmBase
from backend.services.alarm_manager import AlarmManager
from backend.dependencies import get_alarm_manager
from backend.utils.error_handler import ValidationError, AlarmBlockError
from backend.utils.logging import get_logger

# Get module logger
logger = get_logger(__name__)
# Define the router with explicit tags for OpenAPI documentation
router = APIRouter(tags=["alarms"])

class StandardResponse(BaseModel):
    """Standard response model for alarm operations."""
    message: str
    status: str = "success"
    data: Dict[str, Any] = {}

@router.get(
    "/alarms", 
    response_model=List[AlarmBase],
    response_model_exclude_unset=True,
    summary="Get all alarms",
    description="Returns all stored alarms",
    responses={
        status.HTTP_200_OK: {"description": "Successfully retrieved alarms"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to retrieve alarms"}
    }
)
async def get_alarms(
    alarm_manager: AlarmManager = Depends(get_alarm_manager)
):
    """Returns all stored alarms."""
    try:
        alarms = alarm_manager.get_alarms()
        logger.info(f"Retrieved {len(alarms)} alarms", extra={"action": "get_alarms"})
        return [alarm.to_response_model() for alarm in alarms]  # Convert Alarm instances to dicts
    except Exception as e:
        logger.error(f"Error fetching alarms: {e}", extra={"action": "get_alarms", "error": str(e)})
        raise AlarmBlockError("Failed to fetch alarms")

@router.put(
    "/alarm", 
    response_model=StandardResponse,
    summary="Set or update alarm",
    description="Creates a new alarm or updates an existing one",
    responses={
        status.HTTP_200_OK: {"description": "Alarm set successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid alarm data"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to set alarm"}
    }
)
async def set_alarm(
    alarm_data: dict,
    alarm_manager: AlarmManager = Depends(get_alarm_manager)
):
    """Creates or updates an alarm using an Alarm object."""
    try:
        try:
            # Create Alarm object from data
            alarm_obj = Alarm(
                id=alarm_data.get("id"),
                hour=alarm_data.get("hour"),
                minute=alarm_data.get("minute"),
                days=alarm_data.get("days"),
                schedule=alarm_data.get("schedule"),
                active=alarm_data.get("active", True),
            )
        except (ValueError, KeyError) as e:
            logger.error(f"Invalid alarm data: {e}", extra={"action": "set_alarm", "error": str(e)})
            raise ValidationError(f"Invalid alarm data: {e}")
        
        # Set the alarm (AlarmManager handles saving and broadcasting)
        alarm_manager.set_alarm(alarm_obj)
        
        # Log success
        logger.info(f"Alarm set successfully: {alarm_obj.id}", extra={"action": "set_alarm", "alarm_id": alarm_obj.id})
        
        # Return standardized response
        return StandardResponse(
            message="Alarm set successfully",
            data={"alarm": alarm_obj.to_response_model()}
        )
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error setting alarm: {str(e)}")
        raise AlarmBlockError("Failed to set alarm")

@router.delete(
    "/alarms", 
    response_model=StandardResponse,
    summary="Remove alarms",
    description="Removes one or more alarms by ID",
    responses={
        status.HTTP_200_OK: {"description": "Alarms removed successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "Some alarms could not be found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to remove alarms"}
    }
)
async def remove_alarms(
    alarm_ids: List[str],
    alarm_manager: AlarmManager = Depends(get_alarm_manager)
):
    """Removes one or more alarms by ID."""
    try:
        # Remove the alarms (AlarmManager handles saving and broadcasting)
        removed_all = alarm_manager.remove_alarms(alarm_ids)
        
        # Determine response based on result
        if not removed_all:
            logger.warning(
                f"Some alarms could not be removed", 
                extra={"action": "remove_alarms", "alarm_ids": alarm_ids, "removed_all": False}
            )
            return StandardResponse(
                message="Some alarms could not be removed",
                data={"removed_all": False, "alarm_ids": alarm_ids}
            )
        else:
            logger.info(
                f"Alarms removed successfully", 
                extra={"action": "remove_alarms", "alarm_ids": alarm_ids, "removed_all": True}
            )
            return StandardResponse(
                message="Alarms removed successfully",
                data={"removed_all": True, "alarm_ids": alarm_ids}
            )
    except Exception as e:
        logger.error(f"Error removing alarms: {e}", extra={"action": "remove_alarms", "error": str(e)})
        raise AlarmBlockError("Failed to remove alarms")
