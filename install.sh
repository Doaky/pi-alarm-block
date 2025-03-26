#!/bin/bash

# Run the following:
# chmod +x install.sh
# sudo ./install.sh

# Make sure the script is being run as root (sudo)
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run with sudo or as root."
  exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Installing in directory: $PROJECT_DIR"

echo "Installing system dependencies..."
apt update
apt install -y python3 python3-pip python3-dev python3-venv python3-rpi.gpio python3-lgpio nodejs npm

# Create and activate virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv "$PROJECT_DIR/venv"
source "$PROJECT_DIR/venv/bin/activate"

echo "Installing Python packages..."
pip3 install -r "$PROJECT_DIR/requirements.txt"

echo "Setting up frontend..."
cd "$PROJECT_DIR/frontend" || { echo "Frontend directory not found"; exit 1; }

# Install frontend dependencies and build
npm install
npm run build

# Make start script executable
chmod +x "$PROJECT_DIR/start.sh"

# Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/alarm-block.service << EOL
[Unit]
Description=Alarm Block Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/start.sh
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL

# Enable and start the service
systemctl daemon-reload
systemctl enable alarm-block.service
systemctl start alarm-block.service

echo "Installation complete! The service will now start automatically on boot."
echo "You can check the status with: systemctl status alarm-block"
