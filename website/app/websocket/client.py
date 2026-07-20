"""WebSocket client for live dashboard and results updates."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from typing import Any
from urllib.parse import urlencode

from election_platform.logging.setup import get_logger
from election_platform.schemas.websocket import WSMessageType

from app.config.settings import settings
from app.websocket.bus import event_bus

logger = get_logger("website.websocket")

MessageHandler = Callable[[dict[str, Any]], None]


class WebSocketClient:
    """Connect to backend WebSocket with auto-reconnect and event dispatch."""

    def __init__(self, channel: str = "dashboard") -> None:
        base = settings.backend_url.rstrip("/").replace("http://", "ws://").replace("https://", "wss://")
        self.ws_url = f"{base}/ws/{channel}"
        self.channel = channel
        self._handlers: dict[str, list[MessageHandler]] = {}
        self._task: asyncio.Task | None = None
        self._running = False
        self._token: str | None = None

    def on(self, message_type: str, handler: MessageHandler) -> None:
        self._handlers.setdefault(message_type, []).append(handler)

    async def start(self, token: str | None = None) -> None:
        if self._running:
            return
        self._token = token
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def _build_url(self) -> str:
        if not self._token:
            return self.ws_url
        return f"{self.ws_url}?{urlencode({'token': self._token})}"

    async def _run(self) -> None:
        import websockets

        delay = 1.0
        while self._running:
            try:
                async with websockets.connect(self._build_url(), ping_interval=20, ping_timeout=20) as ws:
                    delay = 1.0
                    logger.info("WebSocket connected to %s", self.channel)
                    event_bus.publish("ws_status", {"connected": True, "channel": self.channel})

                    async for raw in ws:
                        if not self._running:
                            break
                        await self._handle_message(raw)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                if not self._running:
                    break
                logger.warning("WebSocket disconnected (%s): %s", self.channel, exc)
                event_bus.publish("ws_status", {"connected": False, "channel": self.channel})
                await asyncio.sleep(delay)
                if not self._running:
                    break
                delay = min(delay * 2, 30.0)

        if self._running:
            event_bus.publish("ws_status", {"connected": False, "channel": self.channel})

    async def _handle_message(self, raw: str) -> None:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Invalid WebSocket payload: %s", raw)
            return

        message_type = str(payload.get("type", ""))
        for handler in self._handlers.get(message_type, []):
            handler(payload)
        for handler in self._handlers.get("*", []):
            handler(payload)
        event_bus.publish(message_type, payload)

    async def send_ping(self) -> None:
        """Reserved for explicit ping support when a socket handle is exposed."""
        event_bus.publish(WSMessageType.PING.value, {})
