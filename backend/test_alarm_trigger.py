#!/usr/bin/env python3
"""
Alarm Trigger Test Script for Raspberry Pi

This script tests the alarm triggering functionality, focusing on conditions
that must be met for an alarm to trigger properly. It helps diagnose issues
with alarm scheduling and triggering.

Usage:
    python test_alarm_trigger.py [--test-type=TYPE]

Options:
    --test-type=TYPE    Type of test to run (default: all)
                        Valid values: all, conditions, scheduler, manual_trigger
"""

import os
import sys
import time
import logging
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('alarm_trigger_test')

# Mock classes for testing
class MockSettingsManager:
    def __init__(self):
        self.is_global_on = True
        self.is_primary_schedule = True
        self.volume = 75
        
    def get_is_global_on(self):
        return self.is_global_on
        
    def set_is_global_on(self, value):
        self.is_global_on = value
        logger.info(f"Global status set to: {value}")
        
    def get_is_primary_schedule(self):
        return self.is_primary_schedule
        
    def set_is_primary_schedule(self, value):
        self.is_primary_schedule = value
        logger.info(f"Primary schedule set to: {value}")
        
    def get_volume(self):
        return self.volume
        
    def set_volume(self, value):
        self.volume = value
        logger.info(f"Volume set to: {value}")

class MockAudioManager:
    def __init__(self):
        self.alarm_playing = False
        self.white_noise_playing = False
        
    def play_alarm(self):
        self.alarm_playing = True
        logger.info("Alarm started playing")
        
    def stop_alarm(self):
        self.alarm_playing = False
        logger.info("Alarm stopped")
        
    def is_alarm_playing(self):
        return self.alarm_playing
        
    def play_white_noise(self):
        self.white_noise_playing = True
        logger.info("White noise started playing")
        return True
        
    def stop_white_noise(self):
        self.white_noise_playing = False
        logger.info("White noise stopped")
        return True
        
    def is_white_noise_playing(self):
        return self.white_noise_playing

def setup_test_environment():
    """Set up the test environment and return the paths."""
    # Get the project root directory
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    project_root = script_dir.parent
    
    # Define paths
    data_dir = project_root / "backend" / "data"
    alarms_file = data_dir / "alarms.json"
    
    # Ensure directories exist
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Alarms file: {alarms_file}")
    
    return {
        'project_root': project_root,
        'data_dir': data_dir,
        'alarms_file': alarms_file
    }

def create_test_alarm(paths, is_primary=True, active=True):
    """Create a test alarm for triggering tests."""
    # Create a simple alarm that would trigger soon
    now = datetime.now()
    trigger_time = now + timedelta(minutes=1)
    
    # Get the day of week (0-6, where Monday is 0)
    day_of_week = now.weekday()
    
    alarm = {
        "id": "test_alarm_1",
        "hour": trigger_time.hour,
        "minute": trigger_time.minute,
        "days": [day_of_week],  # Current day of week
        "is_primary_schedule": is_primary,
        "active": active
    }
    
    # Create another alarm with different settings
    alarm2 = {
        "id": "test_alarm_2",
        "hour": (trigger_time.hour + 1) % 24,  # Next hour
        "minute": trigger_time.minute,
        "days": [day_of_week],  # Current day of week
        "is_primary_schedule": not is_primary,  # Opposite schedule
        "active": active
    }
    
    # Save alarms to file
    alarms = [alarm, alarm2]
    with open(paths['alarms_file'], 'w') as f:
        json.dump(alarms, f, indent=2)
        
    logger.info(f"Created test alarms: {alarms}")
    return alarms

def test_trigger_conditions():
    """Test the conditions required for an alarm to trigger."""
    logger.info("Testing alarm trigger conditions...")
    
    # Create mock managers
    settings_manager = MockSettingsManager()
    audio_manager = MockAudioManager()
    
    # Define test cases
    test_cases = [
        # global_on, primary_schedule, alarm_primary, alarm_active, should_trigger
        (True, True, True, True, True),       # All conditions met
        (False, True, True, True, False),     # Global off
        (True, False, True, True, False),     # Schedule mismatch
        (True, True, False, True, False),     # Schedule mismatch
        (True, True, True, False, False),     # Alarm inactive
    ]
    
    results = []
    
    for case in test_cases:
        global_on, primary_schedule, alarm_primary, alarm_active, should_trigger = case
        
        # Configure settings
        settings_manager.set_is_global_on(global_on)
        settings_manager.set_is_primary_schedule(primary_schedule)
        
        # Create mock alarm
        alarm = {
            "id": "test_alarm",
            "hour": 12,
            "minute": 0,
            "days": [0, 1, 2, 3, 4, 5, 6],
            "is_primary_schedule": alarm_primary,
            "active": alarm_active
        }
        
        # Test trigger logic
        triggered = False
        try:
            # This is the core logic from AlarmManager._trigger_alarm
            if not settings_manager.get_is_global_on():
                logger.info("Alarm trigger blocked (Global Status Off)")
            elif settings_manager.get_is_primary_schedule() != alarm["is_primary_schedule"]:
                logger.info(f"Alarm trigger blocked (Schedule mismatch - current: {settings_manager.get_is_primary_schedule()}, alarm: {alarm['is_primary_schedule']})")
            elif not alarm["active"]:
                logger.info(f"Alarm trigger blocked (Alarm inactive)")
            else:
                logger.info(f"Triggering alarm: {alarm['hour']:02d}:{alarm['minute']:02d} - Primary: {alarm['is_primary_schedule']}")
                audio_manager.play_alarm()
                triggered = True
        except Exception as e:
            logger.error(f"Error in trigger logic: {e}")
            
        # Check result
        result = {
            "case": case,
            "triggered": triggered,
            "expected": should_trigger,
            "passed": triggered == should_trigger
        }
        results.append(result)
        
        # Log result
        if result["passed"]:
            logger.info(f"Test case passed: {case}")
        else:
            logger.error(f"Test case failed: {case}, got {triggered}, expected {should_trigger}")
            
        # Reset audio manager
        audio_manager.stop_alarm()
        
    # Summarize results
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    logger.info(f"Passed {passed}/{total} trigger condition tests")
    
    return passed == total

def test_alarm_scheduler():
    """Test the alarm scheduler functionality."""
    logger.info("Testing alarm scheduler...")
    
    try:
        # Import required modules
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        # Create a scheduler
        scheduler = BackgroundScheduler({'apscheduler.timezone': 'America/New_York'})
        
        # Create a simple job to run in a few seconds
        def test_job():
            logger.info("Test job executed!")
            
        # Get current time
        now = datetime.now()
        trigger_time = now + timedelta(seconds=5)
        
        # Create a trigger
        trigger = CronTrigger(
            hour=trigger_time.hour,
            minute=trigger_time.minute,
            second=trigger_time.second
        )
        
        # Add job
        scheduler.add_job(
            test_job,
            trigger,
            id="test_job"
        )
        
        logger.info(f"Scheduled test job for {trigger_time}")
        
        # Start scheduler
        scheduler.start()
        
        # Wait for job to execute
        logger.info("Waiting for job to execute (10 seconds)...")
        time.sleep(10)
        
        # Check if job executed
        # (We can't directly check this, but we can look at the logs)
        
        # Shutdown scheduler
        scheduler.shutdown()
        logger.info("Scheduler shutdown")
        
        return True
    except Exception as e:
        logger.error(f"Error testing scheduler: {e}")
        return False

def test_manual_trigger():
    """Test manually triggering an alarm."""
    logger.info("Testing manual alarm trigger...")
    
    try:
        # Create mock managers
        settings_manager = MockSettingsManager()
        audio_manager = MockAudioManager()
        
        # Set up test environment
        paths = setup_test_environment()
        
        # Create test alarms
        alarms = create_test_alarm(paths)
        
        # Load the first alarm
        alarm = alarms[0]
        
        # Manually trigger the alarm
        logger.info(f"Manually triggering alarm: {alarm}")
        
        if not settings_manager.get_is_global_on():
            logger.info("Alarm trigger blocked (Global Status Off)")
            return False
            
        if settings_manager.get_is_primary_schedule() != alarm["is_primary_schedule"]:
            logger.info(f"Alarm trigger blocked (Schedule mismatch - current: {settings_manager.get_is_primary_schedule()}, alarm: {alarm['is_primary_schedule']})")
            return False
            
        if not alarm["active"]:
            logger.info(f"Alarm trigger blocked (Alarm inactive)")
            return False
            
        logger.info(f"Triggering alarm: {alarm['hour']:02d}:{alarm['minute']:02d} - Primary: {alarm['is_primary_schedule']}")
        audio_manager.play_alarm()
        
        # Wait a bit
        logger.info("Alarm triggered, waiting 3 seconds...")
        time.sleep(3)
        
        # Check if alarm is playing
        if audio_manager.is_alarm_playing():
            logger.info("Alarm is playing as expected")
            audio_manager.stop_alarm()
            return True
        else:
            logger.error("Alarm is not playing")
            return False
            
    except Exception as e:
        logger.error(f"Error testing manual trigger: {e}")
        return False

def main():
    """Main function to run tests."""
    parser = argparse.ArgumentParser(description='Test alarm triggering on Raspberry Pi')
    parser.add_argument('--test-type', type=str, default='all',
                        help='Type of test to run (all, conditions, scheduler, manual_trigger)')
    
    args = parser.parse_args()
    test_type = args.test_type.lower()
    
    logger.info(f"Starting alarm trigger test with test type: {test_type}")
    
    try:
        # Setup test environment
        paths = setup_test_environment()
        
        # Run tests based on test type
        if test_type in ['all', 'conditions']:
            test_trigger_conditions()
            
        if test_type in ['all', 'scheduler']:
            test_alarm_scheduler()
            
        if test_type in ['all', 'manual_trigger']:
            test_manual_trigger()
            
    except Exception as e:
        logger.error(f"Error during tests: {e}")
        
    logger.info("Alarm trigger tests completed")

if __name__ == "__main__":
    main()
