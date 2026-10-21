"""WebSocket connection and real-time event broadcasting."""

import asyncio
from datetime import datetime, timezone
import logging
from typing import Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("p2p.websocket")


class EventManager:
    """Manages active WebSocket connections and broadcasts real-time events."""

    def __init__(self) -> None:
        self.active_connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept an incoming WebSocket connection and register it."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.debug("WebSocket client connected. Total connections: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from active clients."""
        self.active_connections.discard(websocket)
        logger.debug("WebSocket client disconnected. Total connections: %d", len(self.active_connections))

    async def broadcast(self, event: dict[str, Any]) -> None:
        """Send a JSON payload event to all connected WebSocket clients.

        Event structure: {"type": str, "data": dict, "timestamp": str}
        """
        if "timestamp" not in event:
            event["timestamp"] = datetime.now(timezone.utc).isoformat()

        async with self._lock:
            current_clients = list(self.active_connections)

        failed_clients: list[WebSocket] = []
        for connection in current_clients:
            try:
                await connection.send_json(event)
            except Exception as e:
                logger.warning("Failed to send event to client: %s", e)
                failed_clients.append(connection)

        if failed_clients:
            async with self._lock:
                for failed in failed_clients:
                    self.active_connections.discard(failed)


# Singleton instances for Tracker and Peer WebSocket distribution
tracker_event_manager = EventManager()
peer_event_manager = EventManager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint handler for Tracker event subscriptions."""
    await tracker_event_manager.connect(websocket)
    try:
        while True:
            # Keep connection open and respond to simple client heartbeat pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        tracker_event_manager.disconnect(websocket)
    except Exception as e:
        logger.debug("Tracker WebSocket exception: %s", e)
        tracker_event_manager.disconnect(websocket)


async def peer_websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint handler for local Peer event subscriptions."""
    await peer_event_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        peer_event_manager.disconnect(websocket)
    except Exception as e:
        logger.debug("Peer WebSocket exception: %s", e)
        peer_event_manager.disconnect(websocket)
