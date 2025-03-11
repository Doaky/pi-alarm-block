def is_raspberry_pi():
    try:
        import RPi.GPIO
        return True
    except RuntimeError:
        return False
IS_RASPBERRY_PI = is_raspberry_pi()

import json
from typing import Dict, List
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler

from alarm import Alarm
if IS_RASPBERRY_PI:
    from pi_handler import PiHandler
from settings_manager import SettingsManager

class AlarmManager:
    def __init__(self, settings_manager: SettingsManager, pi_handler = None, file_path: str = "backend/data/alarms.json"):
        self.pi_handler = pi_handler
        self.settings_manager = settings_manager
        self.file_path = file_path

        self.alarms = {}
        self.alarms = self.load_alarms()

        self.scheduler = BackgroundScheduler({'apscheduler.timezone': 'EST'})
        self.scheduler.start()
        self._schedule_set()

    def get_alarms(self) -> List[Alarm]:
        """Get the list of all alarms."""
        return list(self.alarms.values())

    def set_alarm(self, alarm: Alarm) -> None:
        """Adds a new alarm or updates an existing one with the same ID."""
        self.alarms[alarm.id] = alarm
        self._schedule_add(alarm)
        self.save_alarms()

    def remove_alarms(self, alarm_ids: list[str]) -> bool:
        """Removes multiple alarms by their IDs and returns True if all were removed successfully."""
        removed_all = True
        for alarm_id in alarm_ids:
            if alarm_id in self.alarms:
                del self.alarms[alarm_id]
                self._schedule_remove(alarm_id)
            else:
                removed_all = False  # At least one alarm was not found
        self.save_alarms()
        return removed_all
    
    def save_alarms(self) -> None:
        """Saves alarms to a JSON file."""
        try:
            with open(self.file_path, "w") as file:
                json.dump([alarm.to_dict() for alarm in self.alarms.values()], file, indent=4)
        except IOError as e:
            raise IOError(f"Error saving alarms: {e}")
        
    def load_alarms(self) -> List[Dict]:
        """Load alarms from a JSON file."""
        try:
            with open(self.file_path, "r") as file:
                alarms_data = json.load(file)
                print(f"Alarms loaded:\n{alarms_data}\n")
                return {alarm['id']: Alarm.from_dict(alarm) for alarm in alarms_data}
        except (OSError):
            print("Could not open/read file: ", self.file_path,"\n Defaulting to empty")
            return {}
        
    def _schedule_add(self, alarm: Alarm):
        """Add an alarm to the scheduler."""
        trigger = CronTrigger(
            hour=alarm.hour,
            minute=alarm.minute,
            day_of_week=",".join(map(str, alarm.days))
        )
        # Schedule the job to play the alarm sound
        self.scheduler.add_job(self._trigger_alarm, trigger, args=[alarm.id])\
        
    def _schedule_remove(self, alarm_id: str):
        """Remove an alarm from the scheduler."""
        for job in self.scheduler.get_jobs():
            if alarm_id in job.args:
                job.remove()

    def _schedule_set(self):
        """Sets schedule to include all loaded alarms."""
        for alarm in self.alarms.values():
            self._schedule_add(alarm)

    def _trigger_alarm(self, alarm):
        """
        Determines if alarm is valid and plays sound.
        """
        if self.settings_manager.get_is_global_on() == False:
            print("Alarm trigger blocked (Global Status Off).")
            return
        
        is_primary_schedule = self.settings_manager.get_is_primary_schedule()
        if self.settings_manager.get_is_primary_schedule() == alarm.is_primary_schedule:
            print(f"Alarm trigger blocked (Schedule mismatch - schedule is {is_primary_schedule}, alarm is {alarm.is_primary_schedule} )")
            return
        
        if alarm.active == False:
            print(f"Alarm trigger blocked (Alarm innactive)")
            return
        
        print(f"Alarm Triggered: {alarm.hour}:{alarm.minute} - Primary: {alarm.is_primary_schedule}")
        
        # Call function to play the sound
        if self.pi_handler:
            self.pi_handler.play_alarm()

