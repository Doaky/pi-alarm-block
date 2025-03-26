#!/bin/bash

# This script is used to start the alarm block service
# It will be run automatically by systemd
#
# Note: For manual service management, you can use these commands:
# sudo systemctl start alarm-block    # Start the service
# sudo systemctl stop alarm-block     # Stop the service
# sudo systemctl restart alarm-block  # Restart the service
# sudo systemctl status alarm-block   # Check service status
#
# If you need to run frontend and backend separately for development:
# Backend: uvicorn backend.main:app --host 0.0.0.0 --port 8000
# Frontend: cd frontend/dist && python3 -m http.server 8001

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR" || exit 1

# Activate virtual environment
source "$PROJECT_DIR/venv/bin/activate"

# Start the main application (serves both frontend and backend)
echo "Starting Alarm Block service..."
python3 backend/main.py

# Note: No need for process monitoring since we're running
# main.py directly, which handles both frontend and backend
