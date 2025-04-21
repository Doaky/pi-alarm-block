"""WebSocket routes for real-time updates from hardware to frontend."""

import logging

from fastapi import APIRouter, WebSocket

from backend.services.websocket_manager import web_socket_manager
from backend.config import DEV_MODE

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):
    """WebSocket endpoint for real-time updates.
    
    This endpoint handles the complete lifecycle of a WebSocket connection,
    including connection acceptance, message processing, and proper cleanup.
    It uses the WebSocketManager to manage the connection state and ensure
    thread safety.
    """ 
    await web_socket_manager.handle_websocket_lifecycle(websocket, echo_messages=DEV_MODE)

