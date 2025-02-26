#!/bin/bash
# Run the following:
# chmod +x install.sh
# ./install.sh
sudo apt update && sudo apt install -y python3-pip python3-venv nginx
pip3 install fastapi uvicorn RPi.GPIO
cd frontend && npm install && npm run build
