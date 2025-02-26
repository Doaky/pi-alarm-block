import datetime
import time
import threading
from gpio_handler import play_alarm

class AlarmManager:
    def __init__(self):
        self.alarms = []

    def add_alarm(self, hour, minute, days):
        self.alarms.append({"hour": hour, "minute": minute, "days": days})

    def check_alarms(self):
        while True:
            now = datetime.datetime.now()
            for alarm in self.alarms:
                if now.hour == alarm["hour"] and now.minute == alarm["minute"] and now.weekday() in alarm["days"]:
                    play_alarm()
            time.sleep(30)  # Check every 30 seconds

alarm_thread = threading.Thread(target=AlarmManager().check_alarms, daemon=True)
alarm_thread.start()
