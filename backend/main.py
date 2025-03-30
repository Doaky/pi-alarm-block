"""Main entry point for the Alarm Block application."""

import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import time

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.routes import alarm_routes, audio_routes, schedule_routes, system_routes
from backend.dependencies import IS_RASPBERRY_PI
from backend.config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log.level),
    format=config.log.format,
    handlers=[
        logging.FileHandler(config.log.file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Alarm Block API",
    description="API for controlling the Alarm Block system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development. In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request timing and status code."""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"completed in {duration:.3f}s with status {response.status_code}"
    )
    return response

# Add error handling middleware
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include routers with prefixes and tags
app.include_router(
    alarm_routes.router,
    prefix="/api/v1",
    tags=["alarms"]
)
app.include_router(
    audio_routes.router,
    prefix="/api/v1",
    tags=["audio"]
)
app.include_router(
    schedule_routes.router,
    prefix="/api/v1",
    tags=["schedule"]
)
app.include_router(
    system_routes.router,
    prefix="/api/v1",
    tags=["system"]
)

# Health check endpoint
@app.get("/health", tags=["system"])
async def health_check():
    """Check system health."""
    return {
        "status": "healthy",
        "raspberry_pi": IS_RASPBERRY_PI,
        "timestamp": time.time()
    }

# Serve React frontend
app.mount("/", StaticFiles(directory=config.server.frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    try:
        uvicorn.run(
            "main:app",
            host=config.server.host,
            port=config.server.port,
            reload=True,
            log_config=None  # Use our custom logging config
        )
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        raise
