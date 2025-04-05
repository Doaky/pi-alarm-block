"""Main entry point for the Alarm Block application."""

import logging
from pathlib import Path
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import config early to set up environment
from backend.config import config, IS_RASPBERRY_PI, USE_PI_HARDWARE, DEV_MODE

# Import dependencies
from backend.dependencies import get_settings_manager, get_audio_manager, get_alarm_manager
from backend.settings_manager import SettingsManager
from backend.audio_manager import AudioManager
from backend.alarm_manager import AlarmManager

# Import routes
from backend.routes import alarm_routes, schedule_routes, system_routes
from backend.routes.audio_routes import router as audio_router

# Initialize FastAPI application
app = FastAPI(
    title="Alarm Block API",
    description="API for the Alarm Block application",
    version="1.0.0",
    openapi_tags=[
        {"name": "alarms", "description": "Alarm management operations"},
        {"name": "schedules", "description": "Schedule management operations"},
        {"name": "system", "description": "System operations"},
        {"name": "audio", "description": "Audio control operations"},
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api/v1 prefix to match frontend expectations
app.include_router(alarm_routes.router, prefix="/api/v1", tags=["alarms"])
app.include_router(schedule_routes.router, prefix="/api/v1", tags=["schedules"])
app.include_router(system_routes.router, prefix="/api/v1", tags=["system"])
app.include_router(audio_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check(
    request: Request,
    settings_manager: SettingsManager = Depends(get_settings_manager),
    audio_manager: AudioManager = Depends(get_audio_manager),
    alarm_manager: AlarmManager = Depends(get_alarm_manager),
):
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": {
            "dev_mode": DEV_MODE,
            "is_raspberry_pi": IS_RASPBERRY_PI,
            "use_pi_hardware": USE_PI_HARDWARE,
        },
        "components": {
            "settings_manager": settings_manager is not None,
            "audio_manager": audio_manager is not None,
            "alarm_manager": alarm_manager is not None,
        }
    }

# Serve static files
static_dir = Path(__file__).parent.parent / "frontend" / "dist"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
    logger.info(f"Serving static files from {static_dir}")
else:
    logger.warning(f"Static directory {static_dir} does not exist")

if __name__ == "__main__":
    import uvicorn
    # Only use reload in development mode
    if DEV_MODE:
        logger.info("Starting server in development mode with auto-reload enabled")
        uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        logger.info("Starting server in production mode")
        uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
