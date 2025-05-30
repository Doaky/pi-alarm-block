#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Alarm Block Installer ===${NC}"

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
if command -v apt-get &> /dev/null; then
    echo -e "${YELLOW}Debian/Ubuntu detected, installing dependencies...${NC}"
    apt-get update
    apt-get install -y python3 python3-pipx python3-venv python3-dev
elif command -v dnf &> /dev/null; then
    echo -e "${YELLOW}Fedora/RHEL detected, installing dependencies...${NC}"
    dnf install -y python3 python3-pip python3-devel
elif command -v pacman &> /dev/null; then
    echo -e "${YELLOW}Arch Linux detected, installing dependencies...${NC}"
    pacman -Sy --noconfirm python python-pip
else
    echo -e "${RED}Unsupported distribution. Please install dependencies manually.${NC}"
    echo "Required packages: python3, python3-pip, python3-venv, python3-dev"
    exit 1
fi

# Create directories
echo -e "${YELLOW}Creating application directories...${NC}"
mkdir -p /opt/alarm-block
mkdir -p /var/log/alarm-block
mkdir -p /var/lib/alarm-block/data

# Set permissions
chown -R "$REAL_USER:$REAL_USER" /opt/alarm-block
chown -R "$REAL_USER:$REAL_USER" /var/log/alarm-block
chown -R "$REAL_USER:$REAL_USER" /var/lib/alarm-block

# Add user to hardware groups
echo -e "${YELLOW}Adding user to hardware groups...${NC}"

# Check if gpio group exists
if getent group gpio >/dev/null; then
    usermod -aG gpio "$REAL_USER"
else
    echo -e "${YELLOW}gpio group not found, skipping...${NC}"
fi

# Add to audio group
usermod -aG audio "$REAL_USER"

# Copy application files
echo -e "${YELLOW}Copying application files...${NC}"
cp -r backend /opt/alarm-block/
cp -r frontend /opt/alarm-block/
cp pyproject.toml /opt/alarm-block/

# Add entry point if not in pyproject.toml
if ! grep -q "\[project.scripts\]" /opt/alarm-block/pyproject.toml; then
    echo -e "${YELLOW}Adding entry point to pyproject.toml...${NC}"
    echo "" >> /opt/alarm-block/pyproject.toml
    echo "[project.scripts]" >> /opt/alarm-block/pyproject.toml
    echo "alarm-block = \"backend.main:main\"" >> /opt/alarm-block/pyproject.toml
fi

# Install Python application
echo -e "${YELLOW}Installing Python application...${NC}"

# Check if pipx is available, if not install it
if ! command -v pipx &> /dev/null; then
    echo -e "${YELLOW}Installing pipx...${NC}"
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
else
    python -m pipx ensurepath
fi

# Install the application
python -m pipx install /opt/alarm-block

# Configure log rotation
echo -e "${YELLOW}Configuring log rotation...${NC}"
cat > /etc/logrotate.d/alarm-block << EOL
/var/log/alarm-block/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 $REAL_USER $REAL_USER
    su $REAL_USER $REAL_USER
}
EOL

# Create systemd service
echo -e "${YELLOW}Creating systemd service...${NC}"
cat > /etc/systemd/system/alarm-block.service << EOL
[Unit]
Description=Alarm Block Service
After=network.target

[Service]
Type=simple
User=$REAL_USER
WorkingDirectory=/opt/alarm-block
Environment=PYTHONUNBUFFERED=1
Environment=ALARM_BLOCK_LOG_FILE=/var/log/alarm-block/alarm-block.log
Environment=ALARM_BLOCK_DATA_DIR=/var/lib/alarm-block/data
ExecStart=alarm-block
Restart=always
RestartSec=5
StartLimitInterval=0

[Install]
WantedBy=multi-user.target
EOL

# Enable and start service
echo -e "${YELLOW}Enabling and starting service...${NC}"
systemctl daemon-reload
systemctl enable alarm-block.service
systemctl start alarm-block.service

echo -e "${GREEN}Installation complete!${NC}"

echo -e "${GREEN}
          _____                    _____            _____                    _____                    _____                            _____                    _____           _______                   _____                    _____          
         /\    \                  /\    \          /\    \                  /\    \                  /\    \                          /\    \                  /\    \         /::\    \                 /\    \                  /\    \         
        /::\    \                /::\____\        /::\    \                /::\    \                /::\____\                        /::\    \                /::\____\       /::::\    \               /::\    \                /::\____\        
       /::::\    \              /:::/    /       /::::\    \              /::::\    \              /::::|   |                       /::::\    \              /:::/    /      /::::::\    \             /::::\    \              /:::/    /        
      /::::::\    \            /:::/    /       /::::::\    \            /::::::\    \            /:::::|   |                      /::::::\    \            /:::/    /      /::::::::\    \           /::::::\    \            /:::/    /         
     /:::/\:::\    \          /:::/    /       /:::/\:::\    \          /:::/\:::\    \          /::::::|   |                     /:::/\:::\    \          /:::/    /      /:::/~~\:::\    \         /:::/\:::\    \          /:::/    /          
    /:::/__\:::\    \        /:::/    /       /:::/__\:::\    \        /:::/__\:::\    \        /:::/|::|   |                    /:::/__\:::\    \        /:::/    /      /:::/    \:::\    \       /:::/  \:::\    \        /:::/____/           
   /::::\   \:::\    \      /:::/    /       /::::\   \:::\    \      /::::\   \:::\    \      /:::/ |::|   |                   /::::\   \:::\    \      /:::/    /      /:::/    / \:::\    \     /:::/    \:::\    \      /::::\    \           
  /::::::\   \:::\    \    /:::/    /       /::::::\   \:::\    \    /::::::\   \:::\    \    /:::/  |::|___|______            /::::::\   \:::\    \    /:::/    /      /:::/____/   \:::\____\   /:::/    / \:::\    \    /::::::\____\________  
 /:::/\:::\   \:::\    \  /:::/    /       /:::/\:::\   \:::\    \  /:::/\:::\   \:::\____\  /:::/   |::::::::\    \          /:::/\:::\   \:::\ ___\  /:::/    /      |:::|    |     |:::|    | /:::/    /   \:::\    \  /:::/\:::::::::::\    \ 
/:::/  \:::\   \:::\____\/:::/____/       /:::/  \:::\   \:::\____\/:::/  \:::\   \:::|    |/:::/    |:::::::::\____\        /:::/__\:::\   \:::|    |/:::/____/       |:::|____|     |:::|    |/:::/____/     \:::\____\/:::/  |:::::::::::\____\
\::/    \:::\  /:::/    /\:::\    \       \::/    \:::\  /:::/    /\::/   |::::\  /:::|____|\::/    / ~~~~~/:::/    /        \:::\   \:::\  /:::|____|\:::\    \        \:::\    \   /:::/    / \:::\    \      \::/    /\::/   |::|~~~|~~~~~     
 \/____/ \:::\/:::/    /  \:::\    \       \/____/ \:::\/:::/    /  \/____|:::::\/:::/    /  \/____/      /:::/    /          \:::\   \:::\/:::/    /  \:::\    \        \:::\    \ /:::/    /   \:::\    \      \/____/  \/____|::|   |          
          \::::::/    /    \:::\    \               \::::::/    /         |:::::::::/    /               /:::/    /            \:::\   \::::::/    /    \:::\    \        \:::\    /:::/    /     \:::\    \                    |::|   |          
           \::::/    /      \:::\    \               \::::/    /          |::|\::::/    /               /:::/    /              \:::\   \::::/    /      \:::\    \        \:::\__/:::/    /       \:::\    \                   |::|   |          
           /:::/    /        \:::\    \              /:::/    /           |::| \::/____/               /:::/    /                \:::\  /:::/    /        \:::\    \        \::::::::/    /         \:::\    \                  |::|   |          
          /:::/    /          \:::\    \            /:::/    /            |::|  ~|                    /:::/    /                  \:::\/:::/    /          \:::\    \        \::::::/    /           \:::\    \                 |::|   |          
         /:::/    /            \:::\    \          /:::/    /             |::|   |                   /:::/    /                    \::::::/    /            \:::\    \        \::::/    /             \:::\    \                |::|   |          
        /:::/    /              \:::\____\        /:::/    /              \::|   |                  /:::/    /                      \::::/    /              \:::\____\        \::/____/               \:::\____\               \::|   |          
        \::/    /                \::/    /        \::/    /                \:|   |                  \::/    /                        \::/____/                \::/    /         ~~                      \::/    /                \:|   |          
         \/____/                  \/____/          \/____/                  \|___|                   \/____/                          ~~                       \/____/                                   \/____/                  \|___|          
                                                                                                                                                                                                                                                  
${NC}"

echo -e "Service status: $(systemctl status alarm-block.service --no-pager | grep Active)"
echo -e "Check logs with: journalctl -u alarm-block.service"

# Create uninstall script for future use
cat > /opt/alarm-block/uninstall.sh << 'EOL'
#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

echo "Stopping alarm-block service..."
systemctl stop alarm-block.service
systemctl disable alarm-block.service

echo "Removing service file..."
rm -f /etc/systemd/system/alarm-block.service
systemctl daemon-reload

echo "Removing application files..."
pipx uninstall alarm-block
rm -rf /opt/alarm-block
rm -f /etc/logrotate.d/alarm-block

echo "Uninstallation complete!"
echo "Note: Log and data directories (/var/log/alarm-block, /var/lib/alarm-block) were preserved."
echo "To remove them as well, run: rm -rf /var/log/alarm-block /var/lib/alarm-block"
EOL

chmod +x /opt/alarm-block/uninstall.sh
echo -e "${YELLOW}Uninstall script created at /opt/alarm-block/uninstall.sh${NC}"
