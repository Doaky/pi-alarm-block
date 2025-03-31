"""Main entry point for the Alarm Block application."""

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
import subprocess

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.routes import alarm_routes, audio_routes, schedule_routes, system_routes
from backend.dependencies import IS_RASPBERRY_PI
from backend.config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log.level),
    format=config.log.format,
    handlers=[
        logging.FileHandler(str(config.log.file)),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def build_frontend():
    """Build the frontend if dist directory doesn't exist."""
    frontend_dist = project_root / "frontend" / "dist"
    if not frontend_dist.exists():
        logger.info("Frontend dist directory not found. Building frontend...")
        frontend_dir = project_root / "frontend"
        try:
            # Run npm install and build
            subprocess.run(["npm", "install"], cwd=str(frontend_dir), check=True)
            subprocess.run(["npm", "run", "build"], cwd=str(frontend_dir), check=True)
            logger.info("Frontend built successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to build frontend: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error building frontend: {e}")
            return False
    return True

def setup_frontend():
    """Setup frontend files and return if successful."""
    # Build frontend if needed
    if not build_frontend():
        return False

    # Clean and copy frontend files
    frontend_dist = project_root / "frontend" / "dist"
    try:
        # Clean existing files
        if config.server.frontend_dir.exists():
            shutil.rmtree(str(config.server.frontend_dir))
        
        # Copy new files
        logger.info(f"Copying frontend files from {frontend_dist} to {config.server.frontend_dir}")
        shutil.copytree(str(frontend_dist), str(config.server.frontend_dir))
        return True
    except Exception as e:
        logger.error(f"Error setting up frontend files: {e}")
        return False

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
        with open(str(config.log.file), 'r') as f:
            content = f.read()
        return HTMLResponse(f"<pre>{content}</pre>")
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        raise HTTPException(status_code=500, detail="Error reading log file")

# Setup frontend files
frontend_ready = setup_frontend()

# Serve React frontend
if frontend_ready:
    try:
        app.mount("/", StaticFiles(directory=str(config.server.frontend_dir), html=True), name="frontend")
        logger.info(f"Serving frontend from {config.server.frontend_dir}")
    except Exception as e:
        logger.error(f"Error mounting frontend directory: {e}")
        frontend_ready = False

# Serve a basic HTML page if frontend files are missing
if not frontend_ready:
    @app.get("/")
    async def serve_basic_page():
        return HTMLResponse("""
        <html>
            <head>
                <title>Alarm Block</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
                    pre { background: #f5f5f5; padding: 1rem; border-radius: 4px; }
                    .error { color: #dc3545; }
                </style>
            </head>
            <body>
                <h1>Alarm Block</h1>
                <p class="error">Frontend files not found or failed to build.</p>
                <p>To manually build the frontend:</p>
                <pre>
cd frontend
npm install
npm run build
                </pre>
                <p>The API is still accessible at <code>/api/v1/*</code></p>
                <p>View logs at <a href="/logs">/logs</a></p>
                <p>Check health at <a href="/health">/health</a></p>
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
