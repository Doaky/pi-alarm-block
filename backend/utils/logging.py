import logging
import sys
from typing import Optional

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

def setup_logging(level: str = "INFO", module_name: Optional[str] = None) -> logging.Logger:
    """
    Set up colored logging for the specified module.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        module_name: Name of the module to get logger for (if None, returns root logger)
    
    Returns:
        Configured logger instance
    """
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Get the logger
    logger = logging.getLogger(module_name)
    logger.setLevel(numeric_level)
    
    # Only add handler if it doesn't already have one
    if not logger.handlers and not logging.getLogger().handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        
        # Create formatter
        formatter = ColoredFormatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Add formatter to handler
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
    
    return logger
