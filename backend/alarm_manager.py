def is_raspberry_pi():
    try:
        import RPi.GPIO
        return True
    except (RuntimeError, ModuleNotFoundError):
        return False

IS_RASPBERRY_PI = is_raspberry_pi()

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

from backend.alarm import Alarm
from backend.settings_manager import SettingsManager
if IS_RASPBERRY_PI:
    from backend.pi_handler import PiHandler

# Configure logging
logger = logging.getLogger(__name__)

class AlarmManager:
    """Manages alarm scheduling, persistence, and triggering."""

    def __init__(self, settings_manager: SettingsManager, pi_handler = None, file_path: str = "backend/data/alarms.json"):
        """Initialize AlarmManager with settings, hardware interface, and storage path."""
        self.pi_handler = pi_handler
        self.settings_manager = settings_manager
        self.file_path = file_path
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Initialize scheduler with timezone
        self.scheduler = BackgroundScheduler({'apscheduler.timezone': 'EST'})
        self.scheduler.add_listener(self._handle_job_event, 
                                  EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        
        # Load alarms and start scheduler
        self.alarms: Dict[str, Alarm] = {}
        self._load_alarms()
        self._schedule_all_alarms()
        self.scheduler.start()
        
        logger.info("AlarmManager initialized successfully")

    def get_alarms(self) -> List[Alarm]:
        """Get the list of all alarms."""
        return list(self.alarms.values())

    def set_alarm(self, alarm: Alarm) -> None:
        """Add a new alarm or update an existing one."""
        try:
            # Validate alarm data
            if not isinstance(alarm.days, list) or not alarm.days:
                raise ValueError("Alarm must have at least one day selected")
            if not 0 <= alarm.hour <= 23:
                raise ValueError("Hour must be between 0 and 23")
            if not 0 <= alarm.minute <= 59:
                raise ValueError("Minute must be between 0 and 59")
            
            # Update alarm and schedule
            self.alarms[alarm.id] = alarm
            self._schedule_add(alarm)
            self._save_alarms()
            
            logger.info(f"Alarm set successfully: {alarm.id} - {alarm.hour:02d}:{alarm.minute:02d}")
        except Exception as e:
            logger.error(f"Failed to set alarm: {str(e)}")
            raise

    def remove_alarms(self, alarm_ids: List[str]) -> bool:
        """Remove multiple alarms by their IDs."""
        try:
            removed_all = True
            for alarm_id in alarm_ids:
                if alarm_id in self.alarms:
                    del self.alarms[alarm_id]
                    self._schedule_remove(alarm_id)
                    logger.info(f"Alarm removed: {alarm_id}")
                else:
                    removed_all = False
                    logger.warning(f"Alarm not found for removal: {alarm_id}")
            
            self._save_alarms()
            return removed_all
        except Exception as e:
            logger.error(f"Error removing alarms: {str(e)}")
            raise

    def _save_alarms(self) -> None:
        """Save alarms to JSON file with error handling."""
        try:
            with open(self.file_path, "w") as file:
                json.dump([alarm.to_dict() for alarm in self.alarms.values()], 
                         file, indent=4)
            logger.debug("Alarms saved successfully")
        except Exception as e:
            logger.error(f"Failed to save alarms: {str(e)}")
            raise IOError(f"Error saving alarms: {str(e)}")

    def _load_alarms(self) -> None:
        """Load alarms from JSON file with error handling."""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r") as file:
                    alarms_data = json.load(file)
                    self.alarms = {
                        alarm['id']: Alarm.from_dict(alarm) 
                        for alarm in alarms_data
                    }
                logger.info(f"Loaded {len(self.alarms)} alarms")
            else:
                logger.info("No existing alarms file found, starting fresh")
                self.alarms = {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in alarms file: {str(e)}")
            self.alarms = {}
        except Exception as e:
            logger.error(f"Error loading alarms: {str(e)}")
            self.alarms = {}

    def _schedule_add(self, alarm: Alarm) -> None:
        """Add an alarm to the scheduler with error handling."""
        try:
            # Remove any existing jobs for this alarm
            self._schedule_remove(alarm.id)
            
            # Create new trigger
            trigger = CronTrigger(
                hour=alarm.hour,
                minute=alarm.minute,
                day_of_week=",".join(map(str, alarm.days))
            )
            
            # Add new job
            self.scheduler.add_job(
                self._trigger_alarm,
                trigger,
                args=[alarm.id],
                id=str(alarm.id)
            )
            logger.debug(f"Scheduled alarm: {alarm.id}")
        except Exception as e:
            logger.error(f"Failed to schedule alarm {alarm.id}: {str(e)}")
            raise

    def _schedule_remove(self, alarm_id: str) -> None:
        """Remove an alarm from the scheduler."""
        try:
            self.scheduler.remove_job(str(alarm_id))
            logger.debug(f"Removed alarm schedule: {alarm_id}")
        except Exception as e:
            logger.debug(f"No existing schedule for alarm {alarm_id}")

    def _schedule_all_alarms(self) -> None:
        """Schedule all loaded alarms."""
        for alarm in self.alarms.values():
            try:
                self._schedule_add(alarm)
            except Exception as e:
                logger.error(f"Failed to schedule alarm {alarm.id}: {str(e)}")

    def _handle_job_event(self, event) -> None:
        """Handle scheduler job events."""
        if event.exception:
            logger.error(f"Job failed: {event.job_id} - {str(event.exception)}")
        else:
            logger.debug(f"Job completed: {event.job_id}")

    def _trigger_alarm(self, alarm_id: str) -> None:
        """Trigger alarm if conditions are met."""
        try:
            alarm = self.alarms.get(alarm_id)
            if not alarm:
                logger.error(f"Alarm not found: {alarm_id}")
                return

            if not self.settings_manager.get_is_global_on():
                logger.info("Alarm trigger blocked (Global Status Off)")
                return

            is_primary_schedule = self.settings_manager.get_is_primary_schedule()
            if is_primary_schedule != alarm.is_primary_schedule:
                logger.info(f"Alarm trigger blocked (Schedule mismatch - current: {is_primary_schedule}, alarm: {alarm.is_primary_schedule})")
                return

            if not alarm.active:
                logger.info(f"Alarm trigger blocked (Alarm inactive)")
                return

            logger.info(f"Triggering alarm: {alarm.hour:02d}:{alarm.minute:02d} - Primary: {alarm.is_primary_schedule}")
            
            if self.pi_handler:
                self.pi_handler.play_alarm()
            else:
                logger.warning("No hardware interface available for alarm playback")

        except Exception as e:
            logger.error(f"Error triggering alarm {alarm_id}: {str(e)}")

    def cleanup(self) -> None:
        """Clean up resources on shutdown."""
        try:
            self.scheduler.shutdown()
            logger.info("AlarmManager cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def __del__(self):
        """Ensure cleanup on destruction."""
        self.cleanup()
