import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

from backend.alarm import Alarm
from backend.settings_manager import SettingsManager
from backend.audio_manager import AudioManager
from backend.config import USE_PI_HARDWARE

if TYPE_CHECKING:
    from backend.dependencies import HardwareManager

# Configure logging
logger = logging.getLogger(__name__)

class AlarmManager:
    """Manages alarm scheduling, persistence, and triggering."""

    def __init__(
        self,
        settings_manager: SettingsManager,
        audio_manager: AudioManager,
        hardware_manager: Optional['HardwareManager'] = None,
    ):
        """Initialize AlarmManager with settings, audio, and hardware interface."""
        self.settings_manager = settings_manager
        self.audio_manager = audio_manager
        self.hardware_manager = hardware_manager
        
        # Use the project data directory directly
        from backend.config import PROJECT_DATA_DIR
        self.file_path = PROJECT_DATA_DIR / "alarms.json"
        logger.info(f"Using data directory for alarms: {self.file_path}")
        
        # Ensure parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize scheduler with timezone
        self.scheduler = BackgroundScheduler({'apscheduler.timezone': 'EST'})
        self.scheduler.add_listener(
            self._handle_job_event,
            EVENT_JOB_ERROR | EVENT_JOB_EXECUTED
        )
        
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
            
            # Always save alarms to disk after setting an alarm
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

    def _save_alarms(self):
        """Save alarms to file."""
        try:
            # Save as array of alarms instead of dictionary
            data = [alarm.to_dict() for alarm in self.alarms.values()]
            logger.info(f"Saving {len(data)} alarms to {self.file_path}")
            
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=4)
            
            # Verify the file was written correctly
            if self.file_path.exists():
                file_size = self.file_path.stat().st_size
                logger.info(f"Successfully saved alarms to {self.file_path} (size: {file_size} bytes)")
            else:
                logger.error(f"Failed to save alarms: File {self.file_path} does not exist after write")
        except Exception as e:
            logger.error(f"Error saving alarms: {e}")

    def _load_alarms(self):
        """Load alarms from file."""
        try:
            if self.file_path.exists():
                logger.info(f"Loading alarms from {self.file_path}")
                with open(self.file_path, 'r') as f:
                    content = f.read()
                    data = json.loads(content)
                
                # Check if data is a list (array format) or dict (object format)
                if isinstance(data, list):
                    self.alarms = {}
                    for alarm_data in data:
                        alarm = Alarm(**alarm_data)
                        self.alarms[alarm.id] = alarm
                    logger.info(f"Loaded {len(self.alarms)} alarms from array format")
                else:
                    self.alarms = {
                        alarm_id: Alarm(**alarm_data)
                        for alarm_id, alarm_data in data.items()
                    }
                    logger.info(f"Loaded {len(self.alarms)} alarms from dictionary format")
                        
                # logger.info(f"Successfully loaded {len(self.alarms)} alarms from {self.file_path}")            else:
                logger.warning(f"No alarms file found at {self.file_path}, starting with empty alarms")
        except Exception as e:
            logger.error(f"Error loading alarms: {e}")
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
        
            if self.hardware_manager:
                self.hardware_manager.play_alarm()
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
