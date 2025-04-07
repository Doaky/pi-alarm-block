"""WebSocket routes for real-time updates from hardware to frontend."""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from backend.dependencies import get_settings_manager, get_audio_manager, get_alarm_manager
from backend.websocket_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):
    """WebSocket endpoint for real-time updates."""
    try:
        # Accept the connection
        await connection_manager.connect(websocket)
        
        # Keep the connection open and handle messages
        try:
            while True:
                # Wait for messages from the client (ping/pong or other commands)
                data = await websocket.receive_text()
                
                # Simple echo for now - we could handle commands here in the future
                await websocket.send_text(f"Message received: {data}")
                
        except WebSocketDisconnect:
            # Handle normal disconnection
            logger.info("WebSocket client disconnected")
        except Exception as e:
            # Handle other exceptions
            logger.error(f"WebSocket error: {str(e)}")
    finally:
        # Always ensure we disconnect properly
        await connection_manager.disconnect(websocket)

@router.get("/api/v1/alarm/status")
async def get_alarm_status():
    """Get the current alarm status."""
    audio_manager = get_audio_manager()
    is_playing = audio_manager.is_alarm_playing()
    
    return {
        "is_playing": is_playing,
        "mode": "development" if audio_manager._mock_mode else "hardware"
    }
