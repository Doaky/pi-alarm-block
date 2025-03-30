"""Main entry point for the Alarm Block application."""

import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
import uvicorn
import time
import shutil

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
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s")
    return response

# Add error handling middleware
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
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
    tags=["schedules"]
)

app.include_router(
    system_routes.router,
    prefix="/api/v1",
    tags=["system"]
)

@app.get("/health")
async def health_check():
    """Check system health."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "is_raspberry_pi": IS_RASPBERRY_PI
    }

@app.get("/logs")
async def get_logs():
    """View log file contents."""
    try:
        with open(config.log.file, 'r') as f:
            content = f.read()
        return HTMLResponse(f"<pre>{content}</pre>")
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        raise HTTPException(status_code=500, detail="Error reading log file")

# Copy frontend files if they don't exist
frontend_dist = os.path.join(project_root, "frontend", "dist")
if os.path.exists(frontend_dist):
    logger.info(f"Copying frontend files from {frontend_dist} to {config.server.frontend_dir}")
    os.makedirs(config.server.frontend_dir, exist_ok=True)
    for item in os.listdir(frontend_dist):
        src = os.path.join(frontend_dist, item)
        dst = os.path.join(config.server.frontend_dir, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

# Serve React frontend
try:
    app.mount("/", StaticFiles(directory=config.server.frontend_dir, html=True), name="frontend")
    logger.info(f"Serving frontend from {config.server.frontend_dir}")
except Exception as e:
    logger.error(f"Error mounting frontend directory: {e}")
    # Serve a basic HTML page if frontend files are missing
    @app.get("/")
    async def serve_basic_page():
        return HTMLResponse("""
        <html>
            <head><title>Alarm Block</title></head>
            <body>
                <h1>Alarm Block</h1>
                <p>Frontend files not found. Please build the frontend first:</p>
                <pre>
                cd frontend
                npm install
                npm run build
                </pre>
            </body>
        </html>
        """)

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=True
    )
