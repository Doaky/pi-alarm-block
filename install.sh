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
apt-get install -y python3 python3-pip python3-venv python3-dev nodejs npm

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
cp -r frontend /opt/alarm-block/
cp setup.py /opt/alarm-block/

# Create and activate virtual environment
python3 -m venv /opt/alarm-block/venv
source /opt/alarm-block/venv/bin/activate

# Install Python dependencies in the virtual environment
pip install --upgrade pip setuptools wheel
pip install -e /opt/alarm-block

# Create systemd service file
cat > /etc/systemd/system/alarm-block.service << EOL
[Unit]
Description=Alarm Block Service
After=network.target

[Service]
Type=simple
User=$REAL_USER
WorkingDirectory=/opt/alarm-block
Environment=ALARM_BLOCK_LOG_FILE=/var/log/alarm-block/alarm-block.log
Environment=ALARM_BLOCK_DATA_DIR=/var/lib/alarm-block/data
ExecStart=/opt/alarm-block/venv/bin/python -m backend.main
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Enable and start the service
systemctl daemon-reload
systemctl enable alarm-block
systemctl start alarm-block

echo "Installation complete!"
echo "The service is running at http://localhost:8000"
echo "View logs with: journalctl -u alarm-block"
