"""Configuration settings for the Alarm Block application."""

from pathlib import Path
import os
import sys
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from typing import Optional

# Get user-specific directories
USER_HOME = Path.home()
USER_DATA_DIR = USER_HOME / ".local" / "share" / "alarm-block"
USER_LOG_DIR = USER_HOME / ".local" / "log" / "alarm-block"

# Ensure base directories exist
try:
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    USER_LOG_DIR.mkdir(parents=True, exist_ok=True)
    (USER_DATA_DIR / "data").mkdir(exist_ok=True)
    (USER_DATA_DIR / "frontend").mkdir(exist_ok=True)
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
        USER_DATA_DIR / "data",
        description="Data storage directory"
    )

    @validator('data_dir', 'server.frontend_dir', pre=True)
    def validate_directories(cls, v):
        path = Path(v)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Error creating directory {path}: {e}")
        return path

    class Config:
        env_prefix = "ALARM_BLOCK_"
        case_sensitive = False

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

# Export variables for backward compatibility
LOG_FILE = str(config.log.file)
LOG_FORMAT = config.log.format
LOG_LEVEL = config.log.level
DATA_DIR = str(config.data_dir)
FRONTEND_DIR = str(config.server.frontend_dir)
HOST = config.server.host
PORT = config.server.port
