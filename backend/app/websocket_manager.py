import asyncio
import json
from typing import Any

from fastapi import WebSocket

from backend.app.logger import logger


class WebSocketManager:
    """
    Manages active WebSocket connections for live real-time dashboard updates.
    """

    def __init__(self) -> None:
        self.active_connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        if not self.active_connections:
            return

        payload = json.dumps(message)
        dead_connections = set()

        async with self._lock:
            for connection in list(self.active_connections):
                try:
                    await connection.send_text(payload)
                except Exception as exc:
                    logger.debug(f"Error sending message to client: {exc}")
                    dead_connections.add(connection)

            for dead in dead_connections:
                self.active_connections.discard(dead)


ws_manager = WebSocketManager()
