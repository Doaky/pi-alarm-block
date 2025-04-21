import logging
import sys
from logging import Logger
from logging.handlers import TimedRotatingFileHandler
from typing import Dict, Optional

# ANSI color codes for terminal output
COLORS = {
    'DEBUG': '\033[36m',     # Cyan
    'INFO': '\033[32m',      # Green
    'WARNING': '\033[33m',   # Yellow
    'ERROR': '\033[31m',     # Red
    'CRITICAL': '\033[41m',  # Red background
    'RESET': '\033[0m'       # Reset to default
}

class ColoredFormatter(logging.Formatter):
    """
    Custom formatter with colors similar to FastAPI/Uvicorn.
    
    This formatter adds ANSI color codes to log messages based on their level,
    making it easier to distinguish between different types of logs in the console.
    """
    
    def format(self, record):
        # Save the original format
        format_orig = self._style._fmt
        
        # Add colors based on the log level
        if record.levelname in COLORS:
            # Format: timestamp - module - level - message
            self._style._fmt = (
                "%(asctime)s - %(name)s - "
                f"{COLORS[record.levelname]}%(levelname)s{COLORS['RESET']} - "
                "%(message)s"
            )
        
        # Call the original format method
        result = logging.Formatter.format(self, record)
        
        # Restore the original format
        self._style._fmt = format_orig
        
        return result

def setup_logging() -> None:
    """
    One-time logging configuration for the entire application.
    
    This should be called once at application startup. It configures the root logger
    with both console and file handlers based on application configuration.
    
    All modules should use get_logger(__name__) to obtain their logger instances.
    """
    # Import config here to avoid circular imports
    from backend.config import config
    
    # Get the root logger
    root_logger = logging.getLogger()
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:  # Make a copy to avoid modification during iteration
        root_logger.removeHandler(handler)
    
    # Convert string level to logging level
    log_level = getattr(logging, config.log.level.upper(), logging.INFO)
    root_logger.setLevel(logging.DEBUG)  # Root logger gets all messages
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create rotating file handler
    try:
        # Map rotation settings to TimedRotatingFileHandler parameters
        rotation_map: Dict[str, str] = {
            "daily": "D",
            "weekly": "W0",  # Monday
            "monthly": "M"
        }
        
        when = rotation_map.get(config.log.rotation.lower(), "M")
        
        # Create the rotating file handler
        file_handler = TimedRotatingFileHandler(
            filename=str(config.log.file),
            when=when,
            interval=1,  # 1 day, week, or month depending on 'when'
            backupCount=config.log.backup_count,
            encoding="utf-8"
        )
        
        # Set the suffix for rotated files (YYYY-MM-DD format)
        file_handler.suffix = "%Y-%m-%d"
        
        file_handler.setLevel(logging.DEBUG)  # File gets all messages
        # Use root_logger instead of undefined logger variable
        root_logger.debug(f"Log rotation configured: {config.log.rotation} with {config.log.backup_count} backups")
    except (IOError, PermissionError) as e:
        print(f"Warning: Could not create log file at {config.log.file}: {e}")
        file_handler = None
    
    # Create formatters
    if hasattr(config.log, 'colored') and config.log.colored:
        console_formatter = ColoredFormatter(
            fmt=config.log.format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        console_formatter = logging.Formatter(
            fmt=config.log.format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # File always gets plain formatter
    file_formatter = logging.Formatter(
        fmt=config.log.format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Set formatters
    console_handler.setFormatter(console_formatter)
    if file_handler:
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Add handlers
    root_logger.addHandler(console_handler)
    
    # Log setup completion
    root_logger.debug(f"Logging initialized: level={config.log.level}, file={config.log.file}")

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for the specified module.
    
    This is the preferred way to get a logger in all modules.
    
    Args:
        name: Module name, typically __name__
        
    Returns:
        Logger instance configured according to application settings
    """
    return logging.getLogger(name)
