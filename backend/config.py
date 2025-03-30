"""Configuration settings for the Alarm Block application."""

import os
from pathlib import Path
from pydantic import BaseModel, Field, DirectoryPath
from pydantic_settings import BaseSettings
from typing import Optional

# Get user-specific directories
USER_HOME = str(Path.home())
USER_DATA_DIR = os.path.join(USER_HOME, ".local", "share", "alarm-block")
USER_LOG_DIR = os.path.join(USER_HOME, ".local", "log", "alarm-block")

class LogConfig(BaseModel):
    """Logging configuration."""
    file: str = Field(
        os.path.join(USER_LOG_DIR, "alarm-block.log"),
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
    frontend_dir: DirectoryPath = Field(
        os.path.join(USER_DATA_DIR, "frontend"),
        description="Frontend static files directory"
    )

class Config(BaseSettings):
    """Application configuration with environment variable support."""
    log: LogConfig = Field(default_factory=LogConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    data_dir: DirectoryPath = Field(
        os.path.join(USER_DATA_DIR, "data"),
        description="Data storage directory"
    )

    class Config:
        env_prefix = "ALARM_BLOCK_"
        case_sensitive = False

# Create config instance
config = Config()

# Ensure directories exist
os.makedirs(os.path.dirname(config.log.file), exist_ok=True)
os.makedirs(config.data_dir, exist_ok=True)
os.makedirs(config.server.frontend_dir, exist_ok=True)

# Export variables for backward compatibility
LOG_FILE = config.log.file
LOG_FORMAT = config.log.format
LOG_LEVEL = config.log.level
FRONTEND_DIR = str(config.server.frontend_dir)
HOST = config.server.host
PORT = config.server.port
