"""Alarm-related route handlers."""

import logging
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List

from backend.alarm import Alarm, AlarmResponse
from backend.alarm_manager import AlarmManager
from backend.utils.error_handler import ValidationError, AlarmBlockError
from backend.dependencies import get_alarm_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/alarms", response_model=List[AlarmResponse])
async def get_alarms(
    alarm_manager: AlarmManager = Depends(get_alarm_manager)
):
    """Returns all stored alarms."""
    try:
        return alarm_manager.get_alarms()
    except Exception as e:
        logger.error(f"Error fetching alarms: {str(e)}")
        raise AlarmBlockError("Failed to fetch alarms")

@router.put("/set-alarm", response_model=dict)
async def set_alarm(
    alarm_data: dict,
    alarm_manager: AlarmManager = Depends(get_alarm_manager)
):
    """Creates or updates an alarm using an Alarm object."""
    try:
        try:
            alarm_obj = Alarm(
                id=alarm_data.get("id"),
                hour=alarm_data.get("hour"),
                minute=alarm_data.get("minute"),
                days=alarm_data.get("days"),
                is_primary_schedule=alarm_data.get("is_primary_schedule"),
                active=alarm_data.get("active", True),
            )
        except (ValueError, KeyError) as e:
            raise ValidationError(f"Invalid alarm data: {str(e)}")
        
        # Set the alarm and explicitly save it
        alarm_manager.set_alarm(alarm_obj)
        
        # Force a save to ensure it's written to disk
        alarm_manager._save_alarms()
        
        logger.info(f"Alarm set successfully: {alarm_obj.id}")
        return {"message": "Alarm set successfully", "alarm": alarm_obj.to_dict()}
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error setting alarm: {str(e)}")
        raise AlarmBlockError("Failed to set alarm")

@router.delete("/alarms")
async def remove_alarms(
    alarm_ids: List[str],
    alarm_manager: AlarmManager = Depends(get_alarm_manager)
):
    """Deletes alarms by their IDs."""
    try:
        if not alarm_ids:
            raise ValidationError("No alarm IDs provided")
        
        # Remove the alarms
        removed_all = alarm_manager.remove_alarms(alarm_ids)
        
        # Force a save to ensure changes are written to disk
        alarm_manager._save_alarms()
        
        if not removed_all:
            logger.warning(f"Some alarms could not be removed: {alarm_ids}")
            return {"message": "Some alarms could not be removed"}
            
        logger.info(f"Alarms removed successfully: {alarm_ids}")
        return {"message": "Alarms removed successfully"}
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error removing alarms: {str(e)}")
        raise AlarmBlockError("Failed to remove alarms")
