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
    
    async def broadcast_alarm_status(self, is_playing: bool) -> None:
        """Broadcast alarm status update to all connected clients."""
        message = {
            "type": "alarm_status",
            "data": {
                "is_playing": is_playing
            }
        }
        await self.broadcast(message)
        
    async def broadcast_white_noise_status(self, is_playing: bool) -> None:
        """Broadcast white noise status update to all connected clients."""
        message = {
            "type": "white_noise_status",
            "data": {
                "is_playing": is_playing
            }
        }
        await self.broadcast(message)
        
    async def broadcast_volume_update(self, volume: int) -> None:
        """Broadcast volume update to all connected clients."""
        message = {
            "type": "volume_update",
            "data": {
                "volume": volume
            }
        }
        await self.broadcast(message)
        
    async def broadcast_schedule_update(self, schedule: str) -> None:
        """Broadcast schedule update to all connected clients.
        
        Args:
            schedule: Schedule type ('a', 'b', or 'off')
        """
        message = {
            "type": "schedule_update",
            "data": {
                "schedule": schedule
            }
        }
        await self.broadcast(message)
        
    async def broadcast_global_status_update(self, is_on: bool) -> None:
        """Broadcast global alarm status update to all connected clients."""
        message = {
            "type": "global_status_update",
            "data": {
                "is_on": is_on
            }
        }
        await self.broadcast(message)
        
    async def broadcast_alarm_update(self, alarms: list) -> None:
        """Broadcast alarm list update to all connected clients.
        
        Args:
            alarms: List of alarm objects to broadcast
        """
        message = {
            "type": "alarm_update",
            "data": {
                "alarms": alarms
            }
        }
        await self.broadcast(message)
        
    async def broadcast_shutdown(self) -> None:
        """Broadcast system shutdown notification to all connected clients."""
        message = {
            "type": "system_shutdown",
            "data": {
                "shutdown": True
            }
        }
        await self.broadcast(message)

# Create a singleton instance
connection_manager = ConnectionManager()
