import uuid
import logging
from fastapi import WebSocket
from typing import Set


class ConnectionManager:
    """Manages WebSocket connections for real-time event broadcasting."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> str:
        """Accept the WebSocket connection, register it, and send connection-established."""
        await websocket.accept()
        self.active_connections.add(websocket)
        client_id = str(uuid.uuid4())
        await websocket.send_json({
            "type": "connection-established",
            "data": {"client_id": client_id},
        })
        logger.info("WebSocket connected: client_id=%s active=%d", client_id, len(self.active_connections))
        return client_id

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info("WebSocket disconnected: active=%d", len(self.active_connections))

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients.

        Handles disconnected clients gracefully so one broken client
        does not crash broadcasts to others.
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                logger.warning("WebSocket send failed; removing stale connection", exc_info=True)
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.active_connections.discard(connection)


# Global manager instance
manager = ConnectionManager()
logger = logging.getLogger(__name__)
