"""WebSocket client for live updates (placeholder)."""

from website.app.config.settings import settings


class WebSocketClient:
    """Connect to backend WebSocket for live dashboard updates."""

    def __init__(self) -> None:
        self.ws_url = settings.backend_url.replace("http", "ws") + "/ws/dashboard"

    # Implementation deferred to live results phase.
