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

# Create log directory if it doesn't exist
mkdir -p logs

# Set environment variables for development
export ALARM_BLOCK_LOG_FILE="logs/alarm-block.log"
export ALARM_BLOCK_DATA_DIR="data"

echo "Starting development server..."
echo "API and frontend will be available at: http://localhost:8000"
echo "Logs will be written to: logs/alarm-block.log"
echo ""
echo "Press Ctrl+C to stop the server"

# Start the development server with auto-reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
