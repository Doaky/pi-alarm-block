#!/usr/bin/env python3
"""
Diagnostic script for testing alarm scheduling and triggering.
This script creates a test environment to verify that alarms are properly scheduled and triggered.
"""

import os
import sys
import time
import logging
import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("alarm_scheduler_test")

# Ensure we're using the fixed audio manager
os.environ['SDL_AUDIODRIVER'] = 'alsa'

# Add the parent directory to the path so we can import the backend modules
sys.path.append(str(Path(__file__).parent.parent))

from backend.settings_manager import SettingsManager
from backend.audio_manager import AudioManager
from backend.alarm import Alarm
from backend.alarm_manager import AlarmManager

class DiagnosticAlarmManager:
    """Diagnostic class for testing alarm scheduling and triggering."""
    
    def __init__(self):
        """Initialize the diagnostic environment."""
        logger.info("Initializing diagnostic environment")
        
        # Initialize settings manager
        self.settings_manager = SettingsManager()
        logger.info(f"Settings loaded. Global on: {self.settings_manager.get_is_global_on()}, "
                   f"Primary schedule: {self.settings_manager.get_is_primary_schedule()}")
        
        # Ensure global status is on
        if not self.settings_manager.get_is_global_on():
            logger.info("Setting global status to ON")
            self.settings_manager.set_is_global_on(True)
        
        # Initialize audio manager
        self.audio_manager = AudioManager()
        logger.info("Audio manager initialized")
        
        # Initialize alarm manager with our fixed implementation
        self.alarm_manager = AlarmManager(self.settings_manager, self.audio_manager)
        logger.info("Alarm manager initialized")
        
        # Get current scheduler jobs
        self._print_scheduler_jobs()
    
    def _print_scheduler_jobs(self):
        """Print all scheduled jobs."""
        jobs = self.alarm_manager.scheduler.get_jobs()
        logger.info(f"Current scheduled jobs ({len(jobs)}):")
        for job in jobs:
            next_run = job.next_run_time
            next_run_str = next_run.strftime("%Y-%m-%d %H:%M:%S %Z") if next_run else "Not scheduled"
            logger.info(f"  - Job ID: {job.id}, Next run: {next_run_str}")
    
    def test_immediate_alarm(self):
        """Test an alarm that should trigger immediately."""
        logger.info("=== Testing immediate alarm ===")
        
        # Get current time
        now = datetime.datetime.now()
        minute = (now.minute + 1) % 60  # Schedule for the next minute
        hour = now.hour if minute != 0 else (now.hour + 1) % 24
        
        # Get current day of week (0=Monday in our system)
        day_of_week = now.weekday()
        
        # Create a test alarm for the next minute
        test_alarm = Alarm(
            id=None,  # Will generate a new UUID
            hour=hour,
            minute=minute,
            days=[day_of_week],
            is_primary_schedule=self.settings_manager.get_is_primary_schedule(),
            active=True
        )
        
        logger.info(f"Creating test alarm for {hour:02d}:{minute:02d} on day {day_of_week}")
        self.alarm_manager.set_alarm(test_alarm)
        
        # Print scheduler jobs
        self._print_scheduler_jobs()
        
        # Wait for the alarm to trigger
        wait_time = 120  # Wait up to 2 minutes
        logger.info(f"Waiting up to {wait_time} seconds for alarm to trigger...")
        
        start_time = time.time()
        while time.time() - start_time < wait_time:
            # Check every 5 seconds
            time.sleep(5)
            logger.info("Still waiting for alarm trigger...")
            self._print_scheduler_jobs()
        
        logger.info("Test completed")
    
    def test_manual_trigger(self):
        """Test manually triggering an alarm."""
        logger.info("=== Testing manual alarm trigger ===")
        
        # Get all alarms
        alarms = self.alarm_manager.get_alarms()
        
        if not alarms:
            logger.warning("No alarms found to trigger manually")
            return
        
        # Try to trigger the first alarm
        alarm = alarms[0]
        logger.info(f"Manually triggering alarm: {alarm}")
        
        # Directly call the trigger method
        self.alarm_manager._trigger_alarm(alarm.id)
        
        logger.info("Manual trigger test completed")
    
    def test_direct_scheduler(self):
        """Test a direct scheduler implementation."""
        logger.info("=== Testing direct scheduler implementation ===")
        
        # Create a new scheduler
        scheduler = BackgroundScheduler({'apscheduler.timezone': 'America/New_York'})
        
        # Add a listener
        def job_listener(event):
            if event.exception:
                logger.error(f"Direct job failed: {event.job_id} - {str(event.exception)}")
            else:
                logger.info(f"Direct job executed: {event.job_id}")
        
        scheduler.add_listener(job_listener, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)
        
        # Define a simple job function
        def test_job():
            logger.info("Direct test job executed!")
            self.audio_manager.play_alarm()
        
        # Get current time
        now = datetime.datetime.now()
        minute = (now.minute + 1) % 60  # Schedule for the next minute
        hour = now.hour if minute != 0 else (now.hour + 1) % 24
        
        # Schedule the job
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone='America/New_York'
        )
        
        scheduler.add_job(
            test_job,
            trigger,
            id='direct_test_job',
            misfire_grace_time=60
        )
        
        # Start the scheduler
        scheduler.start()
        
        # Print job info
        jobs = scheduler.get_jobs()
        for job in jobs:
            next_run = job.next_run_time
            next_run_str = next_run.strftime("%Y-%m-%d %H:%M:%S %Z") if next_run else "Not scheduled"
            logger.info(f"Direct job: {job.id}, Next run: {next_run_str}")
        
        # Wait for the job to execute
        wait_time = 120  # Wait up to 2 minutes
        logger.info(f"Waiting up to {wait_time} seconds for direct job to execute...")
        
        start_time = time.time()
        while time.time() - start_time < wait_time:
            # Check every 5 seconds
            time.sleep(5)
            logger.info("Still waiting for direct job...")
        
        # Shutdown the scheduler
        scheduler.shutdown()
        logger.info("Direct scheduler test completed")
    
    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up resources")
        self.alarm_manager.cleanup()
        self.audio_manager.cleanup()
        logger.info("Cleanup completed")

def main():
    """Main function to run the diagnostic tests."""
    logger.info("Starting alarm scheduler diagnostic tests")
    
    # Create diagnostic environment
    diagnostic = DiagnosticAlarmManager()
    
    try:
        # Run tests
        diagnostic.test_immediate_alarm()
        time.sleep(5)  # Short pause between tests
        diagnostic.test_manual_trigger()
        time.sleep(5)  # Short pause between tests
        diagnostic.test_direct_scheduler()
    
    finally:
        # Clean up
        diagnostic.cleanup()
    
    logger.info("Diagnostic tests completed")

if __name__ == "__main__":
    main()
