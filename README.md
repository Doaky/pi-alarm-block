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

## Tech Stack

### Frontend
- React 18 with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- React Toastify for notifications
- Modern UI/UX with loading states and animations

### Backend
- FastAPI for RESTful API
- Pydantic for data validation
- Pygame for audio playback
- GPIO for hardware controls
- Thread-safe operations
- Comprehensive logging

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
│   ├── alarm.py        # Alarm class with Pydantic models
│   ├── alarm_manager.py # Alarm scheduling and management
│   ├── audio_manager.py # Thread-safe audio control
│   ├── pi_handler.py   # Hardware interface
│   └── settings_manager.py # Settings with Pydantic models
├── frontend/
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── types/     # TypeScript definitions
│   │   ├── api/       # API integration
│   │   ├── utils/     # Helper functions
│   │   └── styles/    # CSS and Tailwind
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

### Audio Control
- `POST /white-noise/volume`: Adjust white noise volume
- `POST /white-noise/toggle`: Toggle white noise playback
- `GET /white-noise/status`: Get white noise status

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

## Key Features

- Modern, responsive web interface
- Real-time status updates
- Thread-safe audio management
- Comprehensive error handling
- Type safety with TypeScript and Pydantic
- Proper resource management
- Logging for debugging
- Clean component architecture

## License

See LICENSE file for details.
