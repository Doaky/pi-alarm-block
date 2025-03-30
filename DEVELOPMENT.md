# Development Guide

## Environment Setup

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- npm 7 or higher
- Raspberry Pi OS (for production deployment)

### Initial Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/doaky/alarm-block.git
   cd alarm-block
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   ```

3. **Backend Setup**:
   ```bash
   chmod +x dev.sh
   ./dev.sh
   ```

## Development Workflow

### Frontend Development

1. **Development Server**:
   ```bash
   cd frontend
   npm run dev
   ```
   - Access at http://localhost:5173
   - Hot module reloading enabled
   - Changes reflect immediately

2. **Building for Production**:
   ```bash
   npm run build
   ```
   - Output in `frontend/dist`
   - Automatically used by backend

### Backend Development

1. **Start Development Server**:
   ```bash
   ./dev.sh
   ```
   Features:
   - Auto-reload on code changes
   - Local data storage in `./data`
   - Logs in `./logs/alarm-block.log`
   - API docs at http://localhost:8000/docs

2. **Environment Variables**:
   - `ALARM_BLOCK_LOG_FILE`: Log file location
   - `ALARM_BLOCK_DATA_DIR`: Data directory
   - `ALARM_BLOCK_SERVER_FRONTEND_DIR`: Frontend files location

### Testing

1. **Frontend Tests**:
   ```bash
   cd frontend
   npm test
   ```

2. **Backend Tests**:
   ```bash
   pytest backend/tests
   ```

## API Documentation

### Alarm Management

#### GET /api/v1/alarms
Get all configured alarms.
```json
{
  "primary": {
    "enabled": true,
    "time": "07:00",
    "days": ["Mon", "Tue", "Wed", "Thu", "Fri"]
  },
  "secondary": {
    "enabled": false,
    "time": "09:00",
    "days": ["Sat", "Sun"]
  }
}
```

#### PUT /api/v1/alarms
Update alarm configuration.
```json
{
  "schedule": "primary",
  "time": "07:00",
  "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
  "enabled": true
}
```

### Audio Control

#### POST /api/v1/audio/volume
Set white noise volume.
```json
{
  "volume": 0.75  // 0.0 to 1.0
}
```

#### POST /api/v1/audio/white-noise
Toggle white noise playback.
```json
{
  "enabled": true
}
```

### System Control

#### GET /api/v1/status
Get system status.
```json
{
  "active_schedule": "primary",
  "white_noise": {
    "playing": true,
    "volume": 0.75
  },
  "alarm_active": false
}
```

#### GET /api/v1/log
View application logs.
- Query params: `?lines=1000` (default: 1000)
- Returns plain text log content

## Hardware Integration

### GPIO Setup

1. **Rotary Encoder**:
   - Pin A: GPIO 26
   - Pin B: GPIO 6
   - Button: GPIO 13 (White noise toggle)

2. **Switches**:
   - Schedule: GPIO 24 (Primary/Secondary)
   - Status: GPIO 25 (Enable/Disable)

### Testing Hardware

1. Use `gpio` command to test pins:
   ```bash
   gpio readall  # View all pins
   gpio read 24  # Read specific pin
   ```

2. Monitor GPIO events:
   ```bash
   ./dev.sh  # Logs will show GPIO events
   ```

## Debugging

1. **Backend Logs**:
   - Development: `./logs/alarm-block.log`
   - Production: `/var/log/alarm-block/alarm-block.log`
   - Web interface: http://localhost:8000/api/v1/log

2. **Frontend Console**:
   - Chrome DevTools (F12)
   - Network tab for API calls
   - Console for React errors

3. **Service Logs**:
   ```bash
   sudo journalctl -u alarm-block -f
   ```

## Common Issues

1. **ModuleNotFoundError**:
   - Ensure virtual environment is active
   - Check PYTHONPATH in systemd service
   - Reinstall with `pip install -e .`

2. **GPIO Permission Denied**:
   - Add user to gpio group: `sudo usermod -a -G gpio $USER`
   - Use sudo for production install

3. **Audio Issues**:
   - Check ALSA configuration
   - Verify pygame installation
   - Test with `aplay` command
