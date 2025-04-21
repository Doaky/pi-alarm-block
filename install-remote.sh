#!/bin/bash
# One-line installer for Alarm Block
# Usage: curl -sSL https://raw.githubusercontent.com/yourusername/alarm-block/main/install-remote.sh | sudo bash

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Alarm Block One-Line Installer ===${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Get the real user
REAL_USER=${SUDO_USER:-$USER}
if [ "$REAL_USER" = "root" ]; then
    echo -e "${RED}Please run with sudo instead of as root directly${NC}"
    exit 1
fi

# Install git if not present
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}Installing git...${NC}"
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y git
    elif command -v dnf &> /dev/null; then
        dnf install -y git
    elif command -v pacman &> /dev/null; then
        pacman -Sy --noconfirm git
    else
        echo -e "${RED}Unsupported distribution. Please install git manually.${NC}"
        exit 1
    fi
fi

# Create temp directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Clone repository
echo -e "${YELLOW}Cloning alarm-block repository...${NC}"
git clone https://github.com/yourusername/alarm-block.git
cd alarm-block

# Run installer
echo -e "${YELLOW}Running installer...${NC}"
bash install.sh

# Cleanup
cd /
rm -rf "$TEMP_DIR"

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

echo -e "${GREEN}Installation complete!${NC}"
echo -e "To uninstall: sudo /opt/alarm-block/uninstall.sh"
