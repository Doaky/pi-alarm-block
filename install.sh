#!/bin/bash

# Exit on error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Get the user who invoked sudo (or root if not using sudo)
REAL_USER=${SUDO_USER:-$USER}
if [ "$REAL_USER" = "root" ]; then
    echo "Please run this script with sudo instead of as root directly"
    exit 1
fi

# Get user's home directory
USER_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

echo "Installing for user: $REAL_USER"
echo "Home directory: $USER_HOME"

# Install system dependencies
apt-get update
apt-get install -y python3 python3-pip python3-venv python3-dev

# Create directories
mkdir -p /opt/alarm-block
mkdir -p /var/log/alarm-block
mkdir -p /var/lib/alarm-block/data

# Set permissions for the real user
chown -R "$REAL_USER:$REAL_USER" /opt/alarm-block
chown -R "$REAL_USER:$REAL_USER" /var/log/alarm-block
chown -R "$REAL_USER:$REAL_USER" /var/lib/alarm-block

# Copy application files
cp -r backend /opt/alarm-block/
cp -r frontend/dist /opt/alarm-block/frontend/
cp setup.py /opt/alarm-block/

# Create and activate virtual environment
python3 -m venv /opt/alarm-block/venv
source /opt/alarm-block/venv/bin/activate

# Install Python dependencies in the virtual environment
pip install --upgrade pip setuptools wheel
pip install pydantic pydantic-settings fastapi "uvicorn[standard]"
pip install -e /opt/alarm-block

# Deactivate virtual environment
deactivate

# Fix virtual environment permissions
chown -R "$REAL_USER:$REAL_USER" /opt/alarm-block/venv

# Generate systemd service file with current user
cat > /etc/systemd/system/alarm-block.service << EOF
[Unit]
Description=Alarm Block Service
After=network.target

[Service]
Type=simple
User=$REAL_USER
Group=$REAL_USER
WorkingDirectory=/opt/alarm-block
Environment=PATH=/opt/alarm-block/venv/bin:$PATH
Environment=PYTHONPATH=/opt/alarm-block
Environment=HOME=$USER_HOME
ExecStart=/opt/alarm-block/venv/bin/python -m backend.main
Restart=always
RestartSec=3

# Security settings
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/var/log/alarm-block /var/lib/alarm-block
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
EOF

# Start the service
systemctl daemon-reload
systemctl enable alarm-block
systemctl start alarm-block

echo "Installation complete! Service is running at http://localhost:8000"
echo "View logs at: http://localhost:8000/api/v1/log"
echo "Check service status with: systemctl status alarm-block"

echo ""
echo "Virtual environment is at: /opt/alarm-block/venv"
echo "To activate it manually: source /opt/alarm-block/venv/bin/activate"
