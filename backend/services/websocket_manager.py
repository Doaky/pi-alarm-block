import asyncio
import json
import logging
import time
from typing import Dict, List, Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and broadcasts messages to clients for real-time updates."""

    LAST_BROADCAST_TIME: float = 0
    BROADCAST_COOLDOWN = 0.1  # 100ms cooldown
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()
        self.LAST_BROADCAST_TIME = time.time()
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection to accept
            """
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection established. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
        """
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Remaining connections: {len(self.active_connections)}")
        
    async def handle_websocket_lifecycle(self, websocket: WebSocket, echo_messages: bool = True):
        """Handle the complete lifecycle of a WebSocket connection.
        
        This method accepts the connection, monitors for disconnects,
        and ensures proper cleanup when the connection is closed.
        
        Args:
            websocket: WebSocket connection to manage
            echo_messages: If True, echo received messages back to the client
        """
        await self.connect(websocket)
        try:
            while True:
                # This await is crucial for detecting client disconnects
                # even when no messages are being sent
                data = await websocket.receive_text()
                
                # Echo messages back to client if requested
                if echo_messages and data:
                    await websocket.send_text(f"Message received: {data}")
        except WebSocketDisconnect:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
        finally:
            # Ensure connection is always removed
            await self.disconnect(websocket)
    
    async def _broadcast(self, message: Dict[str, Any]):
        """Send a message to all connected clients.
        
        Args:
            message: Dictionary containing the message data
        """
        # Rate limit
        current_time = time.time()
        if current_time - self.LAST_BROADCAST_TIME < self.BROADCAST_COOLDOWN:
            return
        self.LAST_BROADCAST_TIME = current_time
        
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
        """Broadcast alarm status update to all connected clients.
        
        Args:
            is_playing: Boolean indicating if alarm is playing
        """
        message = {
            "type": "alarm_status",
            "data": {
                "is_playing": is_playing
            }
        }
        await self._broadcast(message)
        
    async def broadcast_white_noise_status(self, is_playing: bool) -> None:
        """Broadcast white noise status update to all connected clients.
        
        Args:
            is_playing: Boolean indicating if white noise is playing
        """
        message = {
            "type": "white_noise_status",
            "data": {
                "is_playing": is_playing
            }
        }
        await self._broadcast(message)
        
    async def broadcast_volume_update(self, volume: int) -> None:
        """Broadcast volume update to all connected clients.
        
        Args:
            volume: Volume percentage (0-100)
        """
        message = {
            "type": "volume_update",
            "data": {
                "volume": volume
            }
        }
        await self._broadcast(message)
        
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
        await self._broadcast(message)
        
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
        await self._broadcast(message)
        
    async def broadcast_shutdown(self) -> None:
        """Broadcast system shutdown notification to all connected clients."""
        message = {
            "type": "system_shutdown",
            "data": {
                "shutdown": True
            }
        }
        await self._broadcast(message)

# Create a singleton instance
web_socket_manager = WebSocketManager()
