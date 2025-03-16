def is_raspberry_pi():
    try:
        import RPi.GPIO
        return True
    except (RuntimeError, ModuleNotFoundError):
        return False

IS_RASPBERRY_PI = is_raspberry_pi()

import logging
from fastapi import FastAPI, HTTPException, Body, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from typing import List, Optional
import uvicorn

from alarm import Alarm
from alarm_manager import AlarmManager
from settings_manager import SettingsManager

if IS_RASPBERRY_PI:
    from pi_handler import PiHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alarm_block.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Alarm Block API",
    description="API for controlling the Alarm Block system",
    version="1.0.0"
)

# Initialize managers
settings_manager = SettingsManager()
if IS_RASPBERRY_PI:
    pi_handler = PiHandler(settings_manager)
    logger.info("Initialized PiHandler for Raspberry Pi")
else:
    pi_handler = None
    logger.info("Running in development mode without Raspberry Pi hardware")

alarm_manager = AlarmManager(settings_manager, pi_handler)

### ---- ALARM MANAGEMENT ---- ###
@app.get("/alarms", response_model=List[Alarm])
async def get_alarms():
    """Returns all stored alarms."""
    try:
        return alarm_manager.get_alarms()
    except Exception as e:
        logger.error(f"Error fetching alarms: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alarms"
        )

@app.put("/set-alarm", response_model=dict)
async def set_alarm(alarm_data: dict):
    """Creates or updates an alarm using an Alarm object."""
    try:
        alarm_obj = Alarm(
            id=alarm_data.get("id"),
            hour=alarm_data.get("hour"),
            minute=alarm_data.get("minute"),
            days=alarm_data.get("days"),
            is_primary_schedule=alarm_data.get("is_primary_schedule"),
            active=alarm_data.get("active"),
        )
        
        alarm_manager.set_alarm(alarm_obj)
        logger.info(f"Alarm set successfully: {alarm_obj.id}")
        return {"message": "Alarm set successfully", "alarm": alarm_obj.dict()}
    except KeyError as e:
        logger.error(f"Missing field in alarm data: {e.args[0]}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing field: {e.args[0]}"
        )
    except ValueError as e:
        logger.error(f"Invalid alarm data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error setting alarm: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set alarm"
        )

@app.delete("/alarms")
async def remove_alarms(alarm_ids: List[str]):
    """Deletes alarms by their IDs."""
    try:
        removed_all = alarm_manager.remove_alarms(alarm_ids)
        if not removed_all:
            logger.warning("Some alarms were not found during deletion")
            return JSONResponse(
                status_code=status.HTTP_207_MULTI_STATUS,
                content={"message": "Some alarms were not found", "success": False}
            )
        logger.info(f"Successfully removed alarms: {alarm_ids}")
        return {"message": "Alarms removed successfully", "success": True}
    except Exception as e:
        logger.error(f"Error removing alarms: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove alarms"
        )

### ---- ALARM TRIGGERING ---- ###
@app.post("/stop-alarm")
async def stop():
    """Stops the currently playing alarm."""
    try:
        if IS_RASPBERRY_PI:
            pi_handler.stop_alarm()
            logger.info("Alarm stopped")
            return {"message": "Alarm stopped"}
        return {"message": "No hardware available"}
    except Exception as e:
        logger.error(f"Error stopping alarm: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop alarm"
        )

@app.post("/play-alarm")
async def play():
    """Plays an alarm."""
    try:
        if IS_RASPBERRY_PI:
            pi_handler.play_alarm()
            logger.info("Alarm playing")
            return {"message": "Alarm playing"}
        return {"message": "No hardware available"}
    except Exception as e:
        logger.error(f"Error playing alarm: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to play alarm"
        )

### ---- SCHEDULE & GLOBAL STATUS MANAGEMENT ---- ###
@app.get("/get_schedule")
async def get_schedule():
    """Returns is primary schedule."""
    try:
        return {"is_primary_schedule": settings_manager.get_is_primary_schedule()}
    except Exception as e:
        logger.error(f"Error getting schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get schedule status"
        )

@app.post("/set_schedule")
async def set_schedule(is_primary: bool = Body(..., embed=True)):
    """Updates primary schedule status."""
    try:
        settings_manager.set_is_primary_schedule(is_primary)
        logger.info(f"Schedule set to primary: {is_primary}")
        return {"message": f"Schedule set to primary: {is_primary}"}
    except ValueError as e:
        logger.error(f"Invalid schedule value: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error setting schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set schedule"
        )

@app.get("/get_global_status")
async def get_global_status():
    """Returns is global."""
    try:
        return {"is_global_on": settings_manager.get_is_global_on()}
    except Exception as e:
        logger.error(f"Error getting global status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get global status"
        )

@app.post("/set_global_status")
async def set_global_status(is_global_on: bool = Body(..., embed=True)):
    """Enables or disables all alarms."""
    try:
        settings_manager.set_is_global_on(is_global_on)
        logger.info(f"Global status set to {is_global_on}")
        return {"message": f"Global status set to {is_global_on}"}
    except Exception as e:
        logger.error(f"Error setting global status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set global status"
        )

# Serve React frontend
app.mount("/", StaticFiles(directory="frontend/dist/", html=True), name="frontend")

if __name__ == "__main__":
    try:
        logger.info("Starting Alarm Block server")
        uvicorn.run("main:app", host="0.0.0.0", port=8000)
    except Exception as e:
        logger.error(f"Server startup failed: {str(e)}")
        raise
