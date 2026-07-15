"""Desktop health and diagnostics."""

from __future__ import annotations

import platform
import sys

import requests

from app.config.settings import settings
from app.data.election_store import ElectionStore
from app.health.heartbeat_manager import HeartbeatManager
from app.sync.sync_manager import SyncManager


class DiagnosticsService:
    """Collect node health information for the administrator panel."""

    def __init__(
        self,
        store: ElectionStore,
        sync_manager: SyncManager,
        heartbeat_manager: HeartbeatManager,
        website_url: str,
    ) -> None:
        self.store = store
        self.sync_manager = sync_manager
        self.heartbeat_manager = heartbeat_manager
        self.website_url = website_url.rstrip("/")

    def collect(self) -> dict[str, str]:
        sync_status = self.sync_manager.status()
        heartbeat_status = self.heartbeat_manager.status()
        network_ok = self._check_network()
        return {
            "Platform": platform.platform(),
            "Python": sys.version.split()[0],
            "App Version": settings.app_version,
            "Election ID": self.store.data.get("election_id", "") or "Not downloaded",
            "Election Version": str(self.store.data.get("election_version", 0)),
            "Positions": str(len(self.store.positions)),
            "Candidates": str(len(self.store.candidates)),
            "Queue Size": str(sync_status["queue_size"]),
            "Sync Running": "Yes" if sync_status["running"] else "No",
            "Last Sync": sync_status["last_sync_at"] or "Never",
            "Last Sync Error": sync_status["last_error"] or "None",
            "Heartbeat Running": "Yes" if heartbeat_status["running"] else "No",
            "Heartbeat Online": "Yes" if heartbeat_status["online"] else "No",
            "Last Heartbeat": heartbeat_status["last_success_at"] or "Never",
            "Last Heartbeat Error": heartbeat_status["last_error"] or "None",
            "Website Reachable": "Yes" if network_ok else "No",
            "Website URL": self.website_url,
            "Node ID": self.store.data.get("node_id", "") or "Not configured",
            "Local DB Engine": settings.local_db_engine,
        }

    def _check_network(self) -> bool:
        try:
            response = requests.get(f"{self.website_url}/api/v1/health", timeout=3)
            return response.status_code < 500
        except Exception:
            return False
