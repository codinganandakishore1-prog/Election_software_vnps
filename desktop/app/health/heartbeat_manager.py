"""Periodic node heartbeat transmission with automatic reconnection."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone

from election_platform.enums.sync import SyncStatus
from election_platform.logging.setup import get_logger

from app.config.settings import settings
from app.services.api_client import APIClient, APIClientError
from app.services.local_vote_queue_service import LocalVoteQueueService
from app.sync.node_auth import NodeAuthenticator
from app.sync.retry_manager import RetryManager
from app.sync.sync_manager import SyncManager

logger = get_logger("desktop.heartbeat")


class HeartbeatManager:
    """Send periodic heartbeats to the backend for node health monitoring.

    Heartbeats run independently of vote synchronization and never block voting.
    Failed heartbeats are retried with exponential backoff until the server is
    reachable again.
    """

    def __init__(
        self,
        api_client: APIClient,
        node_authenticator: NodeAuthenticator,
        queue_service: LocalVoteQueueService,
        sync_manager: SyncManager,
        *,
        node_id: str = "",
        config_version: int = 0,
        heartbeat_path: str = "/api/v1/nodes/heartbeat",
        interval_seconds: float | None = None,
        enabled: bool | None = None,
    ) -> None:
        self.api_client = api_client
        self.node_authenticator = node_authenticator
        self.queue_service = queue_service
        self.sync_manager = sync_manager
        self.heartbeat_path = heartbeat_path
        self.node_id = node_id
        self.config_version = config_version
        self.interval_seconds = (
            interval_seconds
            if interval_seconds is not None
            else settings.heartbeat_interval_seconds
        )
        self.enabled = enabled if enabled is not None else settings.heartbeat_enabled
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._consecutive_failures = 0
        self.last_sent_at: str | None = None
        self.last_success_at: str | None = None
        self.last_error: str | None = None
        self.is_online = False

    def start(self) -> None:
        if not self.enabled:
            logger.info("Heartbeat manager disabled")
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker, daemon=True, name="node-heartbeat")
        self._thread.start()
        logger.info("Heartbeat manager started (interval=%ss)", self.interval_seconds)

    def stop(self) -> None:
        self._stop_event.set()

    def update_config(self, *, node_id: str | None = None, config_version: int | None = None) -> None:
        """Refresh node identity included in heartbeat payloads."""
        if node_id is not None:
            self.node_id = node_id
        if config_version is not None:
            self.config_version = config_version

    def status(self) -> dict:
        return {
            "running": bool(self._thread and self._thread.is_alive()),
            "enabled": self.enabled,
            "interval_seconds": self.interval_seconds,
            "online": self.is_online,
            "last_sent_at": self.last_sent_at,
            "last_success_at": self.last_success_at,
            "last_error": self.last_error,
            "consecutive_failures": self._consecutive_failures,
        }

    def _worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                sent = self._send_heartbeat()
                if sent:
                    self._consecutive_failures = 0
                    wait_seconds = self.interval_seconds
                else:
                    wait_seconds = self._failure_backoff()
            except Exception as exc:
                self._record_failure(str(exc))
                wait_seconds = self._failure_backoff()
                logger.warning("Heartbeat error: %s", exc)

            if self._stop_event.wait(wait_seconds):
                break

    def _send_heartbeat(self) -> bool:
        """Attempt to send one heartbeat. Returns True on success."""
        self.last_sent_at = datetime.now(timezone.utc).isoformat()

        if not self.node_id:
            self._record_failure("Node ID is not configured")
            return False

        if not self.node_authenticator.has_credentials:
            self._record_failure("Node credentials are not configured")
            return False

        payload = self._build_payload()
        try:
            headers = self.node_authenticator.auth_headers()
            response = self.api_client.post(self.heartbeat_path, json=payload, headers=headers)
        except APIClientError as exc:
            self._record_failure(str(exc))
            return False

        if response.status_code == 401:
            self.node_authenticator.invalidate()
            try:
                headers = self.node_authenticator.auth_headers()
                response = self.api_client.post(self.heartbeat_path, json=payload, headers=headers)
            except APIClientError as exc:
                self._record_failure(str(exc))
                return False

        if response.status_code >= 500 or response.status_code == 408:
            self._record_failure(f"Server error {response.status_code}")
            return False

        if response.status_code >= 400:
            self._record_failure(f"Heartbeat rejected with status {response.status_code}")
            return False

        self.is_online = True
        self.last_error = None
        self.last_success_at = datetime.now(timezone.utc).isoformat()
        logger.debug("Heartbeat sent for node %s", self.node_id)
        return True

    def _build_payload(self) -> dict:
        queue_status = self.queue_service.queue_status()
        last_vote_time = self.queue_service.get_last_vote_time()
        return {
            "node_id": self.node_id,
            "app_version": settings.app_version,
            "config_version": self.config_version,
            "queue_size": queue_status["queue_size"],
            "last_vote_time": last_vote_time.isoformat() if last_vote_time else None,
            "sync_status": self._derive_sync_status(queue_status["queue_size"]).value,
        }

    def _derive_sync_status(self, queue_size: int) -> SyncStatus:
        if not self.sync_manager.is_online and queue_size > 0:
            return SyncStatus.PENDING
        if not self.is_online and self._consecutive_failures > 0:
            return SyncStatus.OFFLINE
        if queue_size > 0:
            return SyncStatus.SYNCING if self.sync_manager.is_online else SyncStatus.PENDING
        return SyncStatus.HEALTHY

    def _failure_backoff(self) -> float:
        self._consecutive_failures += 1
        return float(RetryManager.backoff_seconds(self._consecutive_failures - 1))

    def _record_failure(self, message: str) -> None:
        self.is_online = False
        self.last_error = message
        logger.debug("Heartbeat failed: %s", message)
