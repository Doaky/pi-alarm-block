#!/bin/bash

# Exit on error
set -e

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing/updating dependencies..."
pip install --upgrade pip setuptools wheel
pip install -e .

# Create local data and log directories if they don't exist
mkdir -p logs
mkdir -p data

# Set environment variables for development
export ALARM_BLOCK_LOG_FILE="logs/alarm-block.log"
export ALARM_BLOCK_DATA_DIR="data"
export ALARM_BLOCK_SERVER_FRONTEND_DIR="frontend/dist"

echo "Starting development server..."
echo "API will be available at: http://localhost:8000"
echo "Logs will be written to: logs/alarm-block.log"
echo ""
echo "Press Ctrl+C to stop the server"

# Start the development server with auto-reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
