# Alarm Block

A modern alarm clock system for Raspberry Pi with dual schedules, white noise, and physical controls.

## Features

- Dual alarm schedules
- White noise playback
- Physical controls via GPIO
- Web interface for configuration
- Systemd service for reliable operation
- Real-time logging and monitoring

## Tech Stack

- **Frontend**: React + Vite + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python
- **Hardware**: Raspberry Pi GPIO for switches and buttons
- **Audio**: Pygame for sound playback

## Quick Start

1. **Development**:
   ```bash
   # Start backend development server
   chmod +x dev.sh
   ./dev.sh

   # In another terminal, start frontend
   cd frontend
   npm install
   npm run dev
   ```

2. **Production**:
   ```bash
   # Build frontend
   cd frontend && npm run build

   # Install service
   sudo ./install.sh
   ```

## Documentation

- [Development Guide](DEVELOPMENT.md) - Detailed setup and development workflow
- [API Documentation](DEVELOPMENT.md#api-documentation) - API endpoints and usage
- [Hardware Setup](DEVELOPMENT.md#hardware-integration) - GPIO configuration
- [Debugging Guide](DEVELOPMENT.md#debugging) - Common issues and solutions

## Directory Structure

- `/backend` - Python backend code
  - `/routes` - API endpoints
  - `/models` - Data models
  - `config.py` - Configuration settings
  - `main.py` - Application entry point

- `/frontend` - React frontend code
  - `/src` - Source code
  - `/dist` - Built files (after `npm run build`)

## System Paths (Production)

- **Application**: `/opt/alarm-block/`
- **Logs**: `/var/log/alarm-block/`
- **Data**: `/var/lib/alarm-block/data/`

## Contributing

1. Read the [Development Guide](DEVELOPMENT.md)
2. Use `dev.sh` for development
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - See LICENSE file for details
