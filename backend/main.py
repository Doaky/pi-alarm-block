from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from alarms import AlarmManager
from gpio_handler import play_alarm, stop_alarm

app = FastAPI()
alarms = AlarmManager()

# Serve React frontend
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="frontend")

@app.get("/alarms")
def get_alarms():
    return alarms.get_alarms()

@app.post("/alarms")
def set_alarm(hour: int, minute: int, days: list[int]):
    alarms.add_alarm(hour, minute, days)
    return {"message": "Alarm set"}

@app.post("/stop-alarm")
def stop():
    stop_alarm()
    return {"message": "Alarm stopped"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
