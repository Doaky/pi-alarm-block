"""Configuration settings for the Alarm Block application."""

from pathlib import Path
import os
import sys
import platform
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any

# Function to detect if running on a Raspberry Pi
def is_raspberry_pi() -> bool:
    """Detect if the current system is a Raspberry Pi."""
    try:
        # Check for Raspberry Pi model in /proc/cpuinfo
        if Path('/proc/cpuinfo').exists():
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo:
                    return True
        
        # Try importing RPi.GPIO as a fallback
        try:
            import RPi.GPIO
            return True
        except (ImportError, RuntimeError):
            pass
        
        return False
    except Exception:
        return False

# Detect platform
IS_RASPBERRY_PI = is_raspberry_pi()

# Get user-specific directories
USER_HOME = Path.home()
USER_DATA_DIR = USER_HOME / ".local" / "share" / "alarm-block"
USER_LOG_DIR = USER_HOME / ".local" / "log" / "alarm-block"

# Project-relative data directory (for settings and alarms)
PROJECT_DATA_DIR = Path(__file__).parent / "data"  # backend/data/

# Ensure base directories exist
try:
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    USER_LOG_DIR.mkdir(parents=True, exist_ok=True)
    (USER_DATA_DIR / "data").mkdir(exist_ok=True)
    (USER_DATA_DIR / "frontend").mkdir(exist_ok=True)
    PROJECT_DATA_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    print(f"Error: Permission denied when creating directories at {USER_DATA_DIR}")
    print("Please ensure you have write permissions to this location or run with sudo.")
    sys.exit(1)
except Exception as e:
    print(f"Error creating directories: {e}")
    sys.exit(1)

class LogConfig(BaseModel):
    """Logging configuration."""
    file: Path = Field(
        USER_LOG_DIR / "alarm-block.log",
        description="Log file path"
    )
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    level: str = Field("INFO", description="Logging level")

class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, ge=1, le=65535, description="Server port")
    frontend_dir: Path = Field(
        USER_DATA_DIR / "frontend",
        description="Frontend static files directory"
    )

class Config(BaseSettings):
    """Application configuration with environment variable support."""
    log: LogConfig = Field(default_factory=LogConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    data_dir: Path = Field(
        PROJECT_DATA_DIR,
        description="Data storage directory"
    )
    dev_mode: bool = Field(
        not IS_RASPBERRY_PI,  # Default to dev mode if not on a Raspberry Pi
        description="Development mode (disables hardware-specific features)"
    )
    force_pi_mode: bool = Field(
        False,
        description="Force Raspberry Pi mode even in development"
    )

    class Config:
        env_prefix = "ALARM_BLOCK_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create config instance
config = Config()

# Create log file if it doesn't exist
try:
    config.log.file.parent.mkdir(parents=True, exist_ok=True)
    if not config.log.file.exists():
        config.log.file.touch()
except Exception as e:
    print(f"Error creating log file: {e}")
    sys.exit(1)

# Ensure directories exist
try:
    if not config.data_dir.exists():
        config.data_dir.mkdir(parents=True, exist_ok=True)
    if not config.server.frontend_dir.exists():
        config.server.frontend_dir.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Error creating directories: {e}")

# Determine if we should use Raspberry Pi hardware features
USE_PI_HARDWARE = (IS_RASPBERRY_PI or config.force_pi_mode) and not config.dev_mode

# Export variables for backward compatibility
LOG_FILE = str(config.log.file)
LOG_FORMAT = config.log.format
LOG_LEVEL = config.log.level
DATA_DIR = str(config.data_dir)
FRONTEND_DIR = str(config.server.frontend_dir)
HOST = config.server.host
PORT = config.server.port

# Export development mode flag for use in other modules
DEV_MODE = config.dev_mode
