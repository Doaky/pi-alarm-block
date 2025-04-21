import json
import threading
from typing import Dict, List, Optional, TYPE_CHECKING, ClassVar

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.models.alarm import Alarm
from backend.services.audio_manager import AudioManager
from backend.services.settings_manager import SettingsManager, ScheduleType
from backend.services.websocket_manager import web_socket_manager
from backend.config import PROJECT_DATA_DIR
from backend.utils.logging import get_logger
from backend.utils.error_handler import AlarmBlockError

if TYPE_CHECKING:
    from backend.dependencies import HardwareManager

# Get module logger
logger = get_logger(__name__)

class AlarmManager:
    """Manages alarm scheduling, persistence, and triggering."""
    
    # Class variable to store the singleton instance
    _instance: ClassVar[Optional['AlarmManager']] = None
    _instance_lock = threading.Lock()

    @classmethod
    def get_instance(cls, settings_manager: Optional[SettingsManager] = None, 
                   audio_manager: Optional[AudioManager] = None,
                   hardware_manager: Optional['HardwareManager'] = None):
        """Get the singleton instance of AlarmManager.
        
        Args:
            settings_manager: Optional settings manager instance
            audio_manager: Optional audio manager instance
            hardware_manager: Optional hardware manager instance
            
        Returns:
            AlarmManager: The singleton instance
        """
        with cls._instance_lock:
            if cls._instance is None:
                if settings_manager is None or audio_manager is None:
                    raise ValueError("settings_manager and audio_manager must be provided when creating the first instance")
                cls._instance = cls(settings_manager, audio_manager, hardware_manager)
            return cls._instance
    
    def __init__(
        self,
        settings_manager: SettingsManager,
        audio_manager: AudioManager,
        hardware_manager: Optional['HardwareManager'] = None,
    ):
        logger.info('AlarmManager __init__ starting')
        """Initialize AlarmManager with settings, audio, and hardware interface.
        
        Note: This should not be called directly. Use get_instance() instead.
        """
        # Check if this is being called through get_instance
        if AlarmManager._instance is not None and AlarmManager._instance is not self:
            logger.warning("AlarmManager should be accessed through get_instance(), not initialized directly")
        self.settings_manager = settings_manager
        self.audio_manager = audio_manager
        self.hardware_manager = hardware_manager

        # Thread lock for thread safety
        self._lock = threading.RLock()
        if not isinstance(self._lock, threading._RLock):
            logger.warning("AlarmManager: self._lock is not an RLock! Deadlocks may occur.")
        
        # Use the project data directory directly
        self.file_path = PROJECT_DATA_DIR / "alarms.json"
        
        # Ensure parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info('AlarmManager: file_path.parent.mkdir done')

        # TODO determine how timezone should be set
        # Initialize scheduler with America/New_York timezone
        logger.info('AlarmManager: initializing BackgroundScheduler')
        self.scheduler = BackgroundScheduler({'apscheduler.timezone': 'America/New_York'})
        self.scheduler.add_listener(
            self._handle_job_event,
            EVENT_JOB_ERROR | EVENT_JOB_EXECUTED
        )
        logger.info('AlarmManager: scheduler and listeners set up')

        # Load alarms and start scheduler
        self.alarms: Dict[str, Alarm] = {}
        logger.info('AlarmManager: about to load alarms')
        self._load_alarms()
        logger.info('AlarmManager: alarms loaded, about to schedule all alarms')
        self._schedule_all_alarms()
        logger.info('AlarmManager: all alarms scheduled, about to start scheduler')
        self.scheduler.start()
        logger.info('AlarmManager: scheduler started')

        logger.info("AlarmManager __init__ finished (initialized successfully)")

    def get_alarms(self) -> List[Alarm]:
        """Get the list of all alarms.
        
        Returns:
            List[Alarm]: List of all configured alarms
        """
        with self._lock:
            logger.debug(f"Retrieved {len(self.alarms)} alarms", extra={"action": "get_alarms"})
            return list(self.alarms.values())

    async def set_alarm(self, alarm: Alarm) -> None:
        """Add a new alarm or update an existing one.
        
        Args:
            alarm: Alarm object to add or update
            
        Raises:
            ValueError: If the alarm data is invalid
            AlarmBlockError: If an error occurs during the operation
        """
        try:
            # Validate alarm data
            if not isinstance(alarm.days, set) or not alarm.days:
                raise ValueError("Alarm must have at least one day selected")
            if not 0 <= alarm.hour <= 23:
                raise ValueError("Hour must be between 0 and 23")
            if not 0 <= alarm.minute <= 59:
                raise ValueError("Minute must be between 0 and 59")
            
            with self._lock:
                # Update alarm and schedule
                self.alarms[alarm.id] = alarm
                self._schedule_add(alarm)
                
                # Save alarms to file
                self._save_alarms()
                
                # Broadcast alarm update to all connected clients
                alarms_dict = [a.to_dict() for a in self.alarms.values()]
                await web_socket_manager.broadcast_alarm_update(alarms_dict)
            
            logger.info(
                f"Alarm set successfully: {alarm.id}", 
                extra={
                    "action": "set_alarm", 
                    "alarm_id": alarm.id,
                    "hour": alarm.hour,
                    "minute": alarm.minute,
                    "days": alarm.days
                }
            )
        except ValueError as e:
            logger.error(f"Invalid alarm data: {e}", extra={"action": "set_alarm", "error": str(e)})
            raise
        except Exception as e:
            logger.error(f"Failed to set alarm: {e}", extra={"action": "set_alarm", "error": str(e)})
            raise AlarmBlockError(f"Failed to set alarm: {e}")

    async def remove_alarms(self, alarm_ids: List[str]) -> bool:
        """Remove multiple alarms by their IDs.
        
        Args:
            alarm_ids: List of alarm IDs to remove
            
        Returns:
            bool: True if all alarms were removed, False otherwise
            
        Raises:
            AlarmBlockError: If an error occurs during the operation
        """
        if not alarm_ids:
            logger.warning("No alarm IDs provided for removal", extra={"action": "remove_alarms"})
            return True
            
        try:
            with self._lock:
                removed_all = True
                for alarm_id in alarm_ids:
                    if alarm_id in self.alarms:
                        del self.alarms[alarm_id]
                        self._schedule_remove(alarm_id)
                        logger.info(f"Alarm removed: {alarm_id}", extra={"action": "remove_alarms", "alarm_id": alarm_id})
                    else:
                        removed_all = False
                        logger.warning(
                            f"Alarm not found for removal: {alarm_id}", 
                            extra={"action": "remove_alarms", "alarm_id": alarm_id, "status": "not_found"}
                        )
                
                # Save alarms to file
                self._save_alarms()
                
                # Broadcast alarm update to all connected clients
                alarms_dict = [a.to_dict() for a in self.alarms.values()]
                await web_socket_manager.broadcast_alarm_update(alarms_dict)
                
            return removed_all
        except Exception as e:
            logger.error(f"Failed to remove alarms: {e}", extra={"action": "remove_alarms", "error": str(e)})
            raise AlarmBlockError(f"Failed to remove alarms: {e}")

    def _save_alarms(self) -> None:
        """Save alarms to file.
        
        Raises:
            Exception: If an error occurs during saving
        """
        try:
            # Lock should be acquired by the calling method
            if not threading.current_thread() == threading.main_thread():
                if not self._lock._is_owned():
                    logger.warning("_save_alarms called without lock", extra={"action": "save_alarms"})
            
            # Convert alarms to serializable format
            alarm_dicts = [alarm.to_dict() for alarm in self.alarms.values()]
            
            # Write to file
            with open(self.file_path, 'w') as f:
                json.dump(alarm_dicts, f, indent=2)
                
            logger.info(
                f"Saved alarms to file", 
                extra={"action": "save_alarms", "count": len(alarm_dicts), "path": str(self.file_path)}
            )
        except Exception as e:
            logger.error(f"Failed to save alarms: {e}", extra={"action": "save_alarms", "error": str(e)})
            raise

    def _load_alarms(self):
        """Load alarms from file."""
        with self._lock:
            # Clear existing alarms to ensure clean state
            self.alarms = {}
            try:
                if self.file_path.exists():
                    logger.info(f"Loading alarms from {self.file_path}")
                    with open(self.file_path, 'r') as f:
                        data = json.load(f)
                    
                    new_alarms = {}
                    for alarm_data in data:
                        try:
                            alarm = Alarm.from_dict(alarm_data)
                            new_alarms[alarm.id] = alarm
                        except ValueError as e:
                            logger.error(f"Invalid alarm data: {e}")
                    self.alarms = new_alarms
                    
                    logger.info(f"Loaded {len(self.alarms)} valid alarms")
                else:
                    logger.warning(f"No alarms file found at {self.file_path}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
            except Exception as e:
                logger.error(f"Error loading alarms: {e}")
            finally:
                logger.info(f"Total alarms after load: {len(self.alarms)}")

    def _schedule_add(self, alarm: Alarm) -> None:
        """Add an alarm to the scheduler with error handling.
        
        Args:
            alarm: Alarm object to schedule
            
        Raises:
            Exception: If an error occurs during scheduling
        """
        with self._lock:
            try:
                # Remove any existing jobs for this alarm
                self._schedule_remove(alarm.id)

                # Log the exact trigger configuration for debugging
                logger.info(f"Scheduling alarm {alarm.id} for {alarm.hour:02d}:{alarm.minute:02d} on days {alarm.days}")
            
                # Create new trigger with explicit timezone
                trigger = CronTrigger(
                    hour=alarm.hour,
                    minute=alarm.minute,
                    day_of_week=",".join(map(str, alarm.days)),
                    timezone='America/New_York' # TODO use config variable
                )
                
                # Add new job
                self.scheduler.add_job(
                    self._trigger_alarm,
                    trigger,
                    args=[alarm.id],
                    id=str(alarm.id),
                    misfire_grace_time=60  # Allow misfires up to 60 seconds
                )
                logger.info(f"Scheduled alarm: {alarm.id} at {alarm.hour:02d}:{alarm.minute:02d}")
            except Exception as e:
                logger.error(f"Failed to schedule alarm {alarm.id}: {str(e)}")
                raise

    def _schedule_remove(self, alarm_id: str) -> None:
        """Remove an alarm from the scheduler.
        
        Args:
            alarm_id: ID of the alarm to remove
        
        Raises:
            Exception: If an error occurs during removal
        """
        with self._lock:
            try:
                self.scheduler.remove_job(str(alarm_id))
                logger.info(f"Removed alarm schedule: {alarm_id}")
            except Exception as e:
                logger.info(f"No existing schedule for alarm {alarm_id}")

    def _schedule_all_alarms(self) -> None:
        """Schedule all loaded alarms.
        
        Raises:
            Exception: If an error occurs during scheduling
        """
        with self._lock:
            logger.debug(f"Scheduling all alarms: {len(self.alarms)} to schedule...")
            for i, alarm in enumerate(self.alarms.values(), 1):
                logger.debug(f"Scheduling alarm {i}/{len(self.alarms)}: {alarm.id}")
                try:
                    self._schedule_add(alarm)
                    logger.debug(f"Alarm {alarm.id} scheduled successfully.")
                except Exception as e:
                    logger.error(f"Failed to schedule alarm {alarm.id}: {str(e)}")
            logger.info(f"All alarms scheduled. Total: {len(self.alarms)}")

    def _handle_job_event(self, event) -> None:
        """Handle scheduler job events.
        
        Args:
            event: Scheduler job event
        """
        if event.exception:
            logger.error(f"Job failed: {event.job_id} - {str(event.exception)}")
        else:
            logger.info(f"Job completed: {event.job_id}")

    def _trigger_alarm(self, alarm_id: str) -> None:
        """Trigger alarm if conditions are met.
        
        Args:
            alarm_id: ID of the alarm to trigger
            
        Raises:
            Exception: If an error occurs during alarm triggering
        """
        try:
            alarm = self.alarms.get(alarm_id)
            if not alarm:
                logger.error(f"Alarm not found: {alarm_id}")
                return
                
            # Get current schedule directly
            schedule = self.settings_manager.get_schedule()
            
            # Check if schedule is OFF
            if schedule == ScheduleType.OFF.value:
                logger.info("Alarm trigger blocked (Schedule is OFF)")
                return

            if schedule != alarm.schedule:
                logger.info(f"Alarm trigger blocked (Schedule mismatch - current: {schedule}, alarm: {alarm.schedule})")
                return

            if not alarm.active:
                logger.info(f"Alarm trigger blocked (Alarm inactive)")
                return

            logger.info(f"Triggering alarm: {alarm.hour:02d}:{alarm.minute:02d} - Schedule: {alarm.schedule}")
        
            # Use audio_manager to play the alarm
            self.audio_manager.play_alarm()

        except Exception as e:
            logger.error(f"Error triggering alarm {alarm_id}: {str(e)}")

    def _cleanup(self) -> None:
        """Clean up resources on shutdown.
        
        Raises:
            Exception: If an error occurs during cleanup
        """
        try:
            self.scheduler.shutdown()
            logger.info("AlarmManager cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def __del__(self):
        """Ensure cleanup on destruction.
        
        Raises:
            Exception: If an error occurs during cleanup
        """
        self._cleanup()
