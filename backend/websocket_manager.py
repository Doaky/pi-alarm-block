"""WebSocket manager for real-time updates from hardware to frontend."""

import asyncio
import json
import logging
from typing import Dict, List, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages to clients."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection established. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Remaining connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Send a message to all connected clients."""
        if not self.active_connections:
            return
            
        # Convert message to JSON string
        json_message = json.dumps(message)
        
        # Use a copy of the connections list to avoid modification during iteration
        async with self._lock:
            connections = self.active_connections.copy()
        
        # Send to all connections, handling disconnects
        disconnect_websockets = []
        for websocket in connections:
            try:
                await websocket.send_text(json_message)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {str(e)}")
                disconnect_websockets.append(websocket)
        
        # Clean up any failed connections
        for websocket in disconnect_websockets:
            await self.disconnect(websocket)
    
    async def broadcast_alarm_status(self, is_playing: bool):
        """Broadcast alarm status update."""
        await self.broadcast({
            "type": "ALARM_STATUS_UPDATE",
            "data": {"is_playing": is_playing}
        })
    
    async def broadcast_white_noise_status(self, is_playing: bool):
        """Broadcast white noise status update."""
        await self.broadcast({
            "type": "WHITE_NOISE_STATUS_UPDATE",
            "data": {"is_playing": is_playing}
        })
    
    async def broadcast_volume_update(self, volume: int):
        """Broadcast volume update."""
        await self.broadcast({
            "type": "VOLUME_UPDATE",
            "data": {"volume": volume}
        })
    
    async def broadcast_schedule_update(self, is_primary: bool):
        """Broadcast schedule update."""
        await self.broadcast({
            "type": "SCHEDULE_UPDATE",
            "data": {"schedule": "a" if is_primary else "b"}
        })
    
    async def broadcast_shutdown(self):
        """Broadcast shutdown notification."""
        await self.broadcast({
            "type": "SYSTEM_SHUTDOWN",
            "data": {"message": "System is shutting down"}
        })

# Create a singleton instance
connection_manager = ConnectionManager()
