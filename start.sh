#!/bin/bash
# Run the following:
# chmod +x start.sh
# ./start.sh

#!/bin/bash

# Ensure the script is being run as root (optional)
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run with sudo or as root."
  exit 1
fi

echo "Starting the project..."

# Step 1: Starting FastAPI server using Uvicorn (this will also start PiHandler and scheduler)
echo "Starting FastAPI server with Uvicorn..."
nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &

# Step 2: Optionally, serve the React frontend if necessary
echo "Serving frontend application..."
cd frontend/dist || { echo "Frontend build directory not found"; exit 1; }
python3 -m http.server 8001 &

# Ensure everything is running
echo "Project started successfully!"

# Optionally: Keep the script running (useful if using nohup or background processes)
tail -f /dev/null
