"""WebSocket connection manager with channel support."""

from __future__ import annotations

from dataclasses import dataclass, field

from election_platform.logging.setup import get_logger
from election_platform.schemas.websocket import WSChannel
from fastapi import WebSocket

logger = get_logger("backend.websocket")


@dataclass
class WebSocketConnection:
    """Tracked WebSocket connection with channel metadata."""

    socket: WebSocket
    channel: WSChannel
    user_id: str | None = None
    role: str | None = None


class ConnectionManager:
    """Manage active WebSocket connections grouped by channel."""

    def __init__(self) -> None:
        self._connections: list[WebSocketConnection] = []

    @property
    def active_connections(self) -> list[WebSocket]:
        """Backward-compatible list of raw sockets."""
        return [connection.socket for connection in self._connections]

    @property
    def connected_count(self) -> int:
        return len(self._connections)

    def connected_count_for(self, channel: WSChannel) -> int:
        return sum(1 for connection in self._connections if connection.channel == channel)

    async def connect(
        self,
        websocket: WebSocket,
        *,
        channel: WSChannel,
        user_id: str | None = None,
        role: str | None = None,
    ) -> WebSocketConnection:
        await websocket.accept()
        connection = WebSocketConnection(
            socket=websocket,
            channel=channel,
            user_id=user_id,
            role=role,
        )
        self._connections.append(connection)
        logger.info(
            "WebSocket connected on %s (total=%s)",
            channel.value,
            self.connected_count,
        )
        return connection

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections = [
            connection for connection in self._connections if connection.socket is not websocket
        ]

    def get_connection(self, websocket: WebSocket) -> WebSocketConnection | None:
        for connection in self._connections:
            if connection.socket is websocket:
                return connection
        return None

    async def send_json(self, websocket: WebSocket, message: dict) -> bool:
        try:
            await websocket.send_json(message)
            return True
        except Exception:
            self.disconnect(websocket)
            return False

    async def broadcast(
        self,
        message: dict,
        *,
        channels: list[WSChannel] | None = None,
    ) -> int:
        """Broadcast a message to one or more channels. Returns delivery count."""
        targets = list(self._connections)
        if channels is not None:
            channel_set = set(channels)
            targets = [connection for connection in targets if connection.channel in channel_set]

        delivered = 0
        for connection in list(targets):
            if await self.send_json(connection.socket, message):
                delivered += 1
        return delivered

    async def broadcast_to_channel(self, channel: WSChannel, message: dict) -> int:
        return await self.broadcast(message, channels=[channel])


manager = ConnectionManager()
