#!/bin/bash

# Run the following:
# chmod +x install.sh
# ./install.sh

# Notes:
# python3 -m venv venv
# source venv/bin/activate
# sudo apt install nodejs npm -y
# sudo apt install python3-lgpio
# sudo apt update
# sudo apt install python3-rpi.gpio
# sudo apt-get install python3-rpi-lgpio
# pactl -- set-sink-volume 0 150%
#speaker-test -c2 -twav -l3
#source venv/bin/activate


# uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload 

# Make sure the script is being run as root (sudo)
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run with sudo or as root."
  exit 1
fi

echo "Installing Python 3 and pip..."
# Update and install Python 3 and pip if not installed
apt update
apt install -y python3 python3-pip python3-dev

echo "Installing required Python packages from requirements.txt..."
# Install the Python packages required for the backend
pip3 install -r requirements.txt

echo "Setting up frontend (React + Vite)..."
# Go to the frontend directory and install npm dependencies
cd frontend || { echo "Frontend directory not found"; exit 1; }

# Ensure Node.js and npm are installed
if ! command -v node &> /dev/null; then
    echo "Node.js not found, installing..."
    curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Install frontend dependencies
npm install

# Build the frontend for production
npm run build

# Go back to the project root directory
cd ..

echo "Installation complete!"

