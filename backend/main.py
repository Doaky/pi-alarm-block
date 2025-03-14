def is_raspberry_pi():
    try:
        import RPi.GPIO
        return True
    except RuntimeError:
        return False
IS_RASPBERRY_PI = is_raspberry_pi()

from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from alarm import Alarm
from alarm_manager import AlarmManager
from settings_manager import SettingsManager
if IS_RASPBERRY_PI:
    from pi_handler import PiHandler

app = FastAPI()
# Enable CORS for frontend communication
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Change to specific frontend URL in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

settings_manager = SettingsManager()


if IS_RASPBERRY_PI:
    pi_handler = PiHandler(settings_manager)
else:
    pi_handler = None

alarm_manager = AlarmManager(settings_manager, pi_handler)

### ---- ALARM MANAGEMENT ---- ###
@app.get("/alarms")
def get_alarms():
    """Returns all stored alarms."""
    return alarm_manager.get_alarms()

@app.put("/set-alarm")
def set_alarm(alarm_data: dict):
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
        return {"message": "Alarm set successfully"}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {e.args[0]}")

@app.delete("/alarms")
def remove_alarms(alarm_ids: List[str]):
    """Deletes alarms by their IDs."""
    removed_all = alarm_manager.remove_alarms(alarm_ids)
    if not removed_all:
        return {"message": "Some alarms were not found", "success": False}
    return {"message": "Alarms removed successfully", "success": True}


### ---- ALARM TRIGGERING ---- ###
@app.post("/stop-alarm")
def stop():
    """Stops the currently playing alarm."""
    if IS_RASPBERRY_PI:
        pi_handler.stop_alarm()
    return {"message": "Alarm stopped"}

@app.post("/play-alarm")
def play():
    """Plays an alarm."""
    if IS_RASPBERRY_PI:
        pi_handler.play_alarm()
    return {"message": "Alarm playing"}


### ---- SCHEDULE & GLOBAL STATUS MANAGEMENT ---- ###
@app.get("/get_schedule")
def get_schedule():
    """Returns is primary schedule."""
    return {"is_primary_schedule": settings_manager.get_is_primary_schedule()}

@app.post("/set_schedule")
def set_schedule(is_primary: bool = Body(..., embed=True)):
    """Updates primary schedule status."""
    try:
        settings_manager.set_is_primary_schedule(is_primary)
        return {"message": f"Schedule set to primary: {is_primary}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/get_global_status")
def get_global_status():
    """Returns is global."""
    return {"is_global_on": settings_manager.get_is_global_on()}

@app.post("/set_global_status")
def set_global_status(is_global_on: bool = Body(...,  embed=True)):
    """Enables or disables all alarms."""
    settings_manager.set_is_global_on(is_global_on)
    return {"message": f"Global status set to {is_global_on}"}

# Serve React frontend
app.mount("/", StaticFiles(directory="frontend/dist/", html=True), name="frontend")



### ---- SERVER STARTUP ---- ###
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
