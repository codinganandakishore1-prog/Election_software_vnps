"""Page-scoped WebSocket subscription lifecycle helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from election_platform.logging.setup import get_logger

from app.websocket.bus import event_bus

logger = get_logger("website.websocket")


def safe_ui_update(callback: Callable[[], None]) -> None:
    """Run a UI callback; ignore errors when the browser client was deleted."""
    try:
        callback()
    except RuntimeError as exc:
        message = str(exc).lower()
        if "client" in message and "deleted" in message:
            return
        raise
    except Exception as exc:
        logger.debug("Skipped UI update after page disconnect: %s", exc)


class WebSocketPageSession:
    """Track page lifecycle for event-bus subscriptions and UI-safe handlers."""

    def __init__(self) -> None:
        self.active = True
        self._subscriptions: list[tuple[str, Callable[[dict[str, Any]], None]]] = []

    def bind(self, handler: Callable[[dict[str, Any]], None]) -> Callable[[dict[str, Any]], None]:
        """Wrap a handler so it ignores calls after the page disconnects."""

        def wrapped(payload: dict[str, Any]) -> None:
            if not self.active:
                return
            safe_ui_update(lambda: handler(payload))

        return wrapped

    def subscribe(self, event_type: str, handler: Callable[[dict[str, Any]], None]) -> None:
        wrapped = self.bind(handler)
        self._subscriptions.append((event_type, wrapped))
        event_bus.subscribe(event_type, wrapped)

    def deactivate(self) -> None:
        self.active = False
        for event_type, callback in self._subscriptions:
            event_bus.unsubscribe(event_type, callback)
        self._subscriptions.clear()
