"""System-related route handlers."""

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from typing import Optional

from backend.config import config

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
