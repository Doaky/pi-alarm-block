# Alarm Block

A full-stack alarm clock application designed for Raspberry Pi 0W with physical controls and modern web interface.

## Features

- **Dual Alarm Schedules**: Switch between primary and secondary alarm schedules
- **Physical Controls**:
  - Three-Way Switch: Toggle between Primary/Secondary Schedule and Silent Mode
  - Rotary Encoder: Adjust white noise volume and toggle playback
  - Dismiss Button: Stop active alarms
- **White Noise**: Built-in white noise playback with volume control
- **Modern Web Interface**: Clean, responsive UI built with React and Tailwind CSS
- **Hardware Integration**: Full GPIO support for physical controls

## Hardware Setup

### GPIO Pin Configuration
- GPIO 26: Rotary Encoder Pin A
- GPIO 6: Rotary Encoder Pin B
- GPIO 13: Rotary Encoder Button (White Noise Toggle)
- GPIO 24: Schedule Switch
- GPIO 25: Global Status Switch

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Doaky/alarm-block.git
cd alarm-block
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

4. Build the frontend:
```bash
npm run build
```

5. Start the application:
```bash
cd ..
./start.sh
```

## Project Structure

```
alarm-block/
├── backend/
│   ├── data/           # JSON storage for alarms and settings
│   ├── sounds/         # Alarm and white noise audio files
│   ├── main.py         # FastAPI application entry point
│   ├── alarm.py        # Alarm class definition
│   ├── alarm_manager.py # Alarm scheduling and management
│   ├── pi_handler.py   # Hardware interface and audio control
│   └── settings_manager.py # Application settings management
├── frontend/
│   ├── src/
│   │   ├── App.tsx    # Main React application
│   │   └── ...        # Other React components
│   └── ...
└── README.md
```

## API Endpoints

### Alarm Management
- `GET /alarms`: Retrieve all alarms
- `PUT /set-alarm`: Create or update an alarm
- `DELETE /alarms`: Delete specified alarms

### Control
- `POST /stop-alarm`: Stop currently playing alarm
- `POST /play-alarm`: Trigger alarm playback
- `GET /get_schedule`: Get current schedule status
- `POST /set_schedule`: Set primary/secondary schedule
- `GET /get_global_status`: Get global alarm status
- `POST /set_global_status`: Enable/disable all alarms

## Frontend-Backend Communication

The frontend communicates with the backend through RESTful API endpoints. The FastAPI backend serves the React frontend as static files, creating a single unified application. All API requests are made to the same origin, eliminating CORS concerns in production.

## Development

For development:

1. Start the backend:
```bash
python backend/main.py
```

2. Start the frontend development server:
```bash
cd frontend
npm run dev
```

## License

See LICENSE file for details.
