"""System-related route handlers."""

import logging
import os
import signal
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Optional

from backend.config import config, IS_RASPBERRY_PI
from backend.dependencies import _instances

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/log", response_class=PlainTextResponse)
async def view_logs(lines: Optional[int] = 1000):
    """View the application log file. Default to last 1000 lines."""
    try:
        log_path = Path(config.log.file)
        if not log_path.exists():
            raise HTTPException(status_code=404, detail="Log file not found")
        
        with open(log_path, 'r') as f:
            # Read all lines and get the last N lines
            all_lines = f.readlines()
            last_n_lines = all_lines[-lines:] if lines else all_lines
            return ''.join(last_n_lines)
            
    except Exception as e:
        logger.error(f"Error reading log file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to read log file")


def shutdown_application():
    """Safely shutdown the application by cleaning up resources and exiting."""
    logger.info("Shutdown requested - cleaning up resources...")
    
    # Clean up all manager instances
    for name, instance in _instances.items():
        logger.info(f"Cleaning up {name}...")
        if hasattr(instance, 'cleanup') and callable(instance.cleanup):
            try:
                instance.cleanup()
                logger.info(f"Successfully cleaned up {name}")
            except Exception as e:
                logger.error(f"Error cleaning up {name}: {str(e)}")
    
    # Commented out: Code for safely shutting down the Raspberry Pi
    # if IS_RASPBERRY_PI:
    #     logger.info("Shutting down Raspberry Pi...")
    #     try:
    #         # Use os.system to run the shutdown command
    #         os.system("sudo shutdown -h now")
    #     except Exception as e:
    #         logger.error(f"Error shutting down Raspberry Pi: {str(e)}")
    
    # Exit the application
    logger.info("Application shutdown complete. Exiting...")
    # Use SIGTERM to allow for clean exit
    os.kill(os.getpid(), signal.SIGTERM)


@router.post("/shutdown", status_code=202)
async def shutdown(background_tasks: BackgroundTasks):
    """Shutdown the application safely."""
    logger.info("Shutdown endpoint called")
    
    # Add the shutdown task to run in the background after response is sent
    background_tasks.add_task(shutdown_application)
    
    return JSONResponse(
        status_code=202,
        content={"message": "Shutdown initiated", "status": "success"}
    )
