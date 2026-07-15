"""In-process event bus for WebSocket messages."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any


class EventBus:
    """Simple publish/subscribe bus for WebSocket events."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[dict[str, Any]], None]]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable[[dict[str, Any]], None]) -> None:
        if callback not in self._listeners[event_type]:
            self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[dict[str, Any]], None]) -> None:
        if callback in self._listeners[event_type]:
            self._listeners[event_type].remove(callback)

    def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        for callback in list(self._listeners[event_type]):
            callback(payload)
        for callback in list(self._listeners["*"]):
            callback({"type": event_type, **payload})


event_bus = EventBus()
