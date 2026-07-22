"""WebSocket message type definitions shared across backend and website."""

from enum import Enum


class WSMessageType(str, Enum):
    """Canonical WebSocket event types."""

    CONNECTED = "connected"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"

    DASHBOARD_SNAPSHOT = "dashboard_snapshot"
    VOTE_SYNCED = "vote_synced"
    VOTE_COUNTS = "vote_counts"
    HEARTBEAT_RECEIVED = "heartbeat_received"
    NODE_STATUS = "node_status"
    SYNC_STATUS = "sync_status"
    NOTIFICATION = "notification"
    LIVE_RESULTS_UPDATE = "live_results_update"
    ELECTION_STATUS = "election_status"


class WSChannel(str, Enum):
    """WebSocket audience channels."""

    DASHBOARD = "dashboard"
    LIVE = "live"
