import asyncio
import os
import signal
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import PlainTextResponse

from backend.config import config
from backend.services.websocket_manager import web_socket_manager
from backend.utils.logging import get_logger

# Get module logger
logger = get_logger(__name__)
router = APIRouter()

def read_last_n_lines(file_path: Path, n: int) -> List[str]:
    """Efficiently read the last N lines from a file without loading the entire file.
    
    Args:
        file_path: Path to the file
        n: Number of lines to read from the end
        
    Returns:
        List of the last n lines
    """
    try:
        # Get file size
        file_size = file_path.stat().st_size
        
        if file_size == 0:
            return []
            
        # Start with a reasonable buffer size
        avg_line_length = 150  # Estimated average line length
        buffer_size = avg_line_length * n
        
        # Don't try to read more than the file size
        buffer_size = min(buffer_size, file_size)
        
        # Position to start reading from
        position = max(file_size - buffer_size, 0)
        
        # Read the last chunk of the file
        with open(file_path, 'r', encoding='utf-8') as f:
            # Seek to position
            f.seek(position)
            
            # Read the rest of the file
            lines = f.readlines()
            
            # If we didn't start at the beginning, we might have a partial line
            if position > 0 and lines:
                # Discard the potentially partial first line
                lines = lines[1:]
                
            # Return the last n lines or all lines if fewer
            return lines[-n:] if len(lines) > n else lines
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []

@router.get("/log", response_class=PlainTextResponse, 
             responses={
                 200: {"description": "Log file contents"},
                 404: {"description": "Log file not found"},
                 500: {"description": "Server error"}
             })
async def view_logs(lines: Optional[int] = 1000) -> str:
    """View the application log file. Default to last 1000 lines.
    
    Args:
        lines: Number of lines to display from the end of the log file
        
    Returns:
        String containing the requested log lines
        
    Raises:
        HTTPException: If the log file cannot be accessed or read
    """
    if lines is not None and lines <= 0:
        lines = 1000  # Default to 1000 lines if invalid value provided
        
    try:
        log_path = Path(config.log.file)
        
        if not log_path.exists():
            logger.warning(f"Log file not found: {log_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Log file not found"
            )
        
        # Get the last N lines efficiently
        last_lines = read_last_n_lines(log_path, lines or 1000)
        return ''.join(last_lines)
            
    except FileNotFoundError:
        logger.warning(f"Log file not found: {config.log.file}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Log file not found"
        )
    except PermissionError as e:
        logger.error(f"Permission denied accessing log file: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Permission denied accessing log file"
        )
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to read log file"
        )


# Track registered services that need cleanup
_cleanup_handlers: Dict[str, Any] = {}

def register_for_cleanup(name: str, instance: Any) -> None:
    """Register a service instance for cleanup during shutdown.
    
    Args:
        name: Name of the service for logging
        instance: Service instance that has a cleanup() method
    """
    if hasattr(instance, 'cleanup') and callable(instance.cleanup):
        _cleanup_handlers[name] = instance
        logger.debug(f"Registered {name} for shutdown cleanup")

async def shutdown_application() -> None:
    """Safely shutdown the application by cleaning up resources and exiting."""
    logger.info("Shutdown requested - cleaning up resources...")
    
    # First, broadcast shutdown notification to all connected clients
    try:
        logger.info("Broadcasting shutdown notification...")
        await web_socket_manager.broadcast_shutdown()
        # Add a small delay to ensure the message is sent
        await asyncio.sleep(1)
        logger.info("Shutdown notification sent successfully")
    except Exception as e:
        logger.error(f"Error broadcasting shutdown notification: {e}")
    
    # Clean up all registered services
    for name, instance in _cleanup_handlers.items():
        logger.info(f"Cleaning up {name}...")
        try:
            instance.cleanup()
            logger.info(f"Successfully cleaned up {name}")
        except Exception as e:
            logger.error(f"Error cleaning up {name}: {e}")
    
    # TODO enable Raspberry Pi shutdown
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


@router.post("/shutdown", status_code=status.HTTP_202_ACCEPTED,
             responses={
                 202: {"description": "Shutdown initiated"},
             })
async def shutdown(background_tasks: BackgroundTasks) -> Dict[str, str]:
    """Shutdown the application safely.
    
    This endpoint initiates a graceful shutdown process:
    1. Returns a 202 Accepted response immediately
    2. Broadcasts a shutdown message to all connected clients
    3. Cleans up all registered services
    4. Terminates the application
    
    Args:
        background_tasks: FastAPI background tasks manager
        
    Returns:
        Dict with status message
    """
    logger.info("Shutdown endpoint called")
    
    # Add the shutdown task to run in the background after response is sent
    background_tasks.add_task(shutdown_application)
    
    return {"message": "Shutdown initiated", "status": "success"}
