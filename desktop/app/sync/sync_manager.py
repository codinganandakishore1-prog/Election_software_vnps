"""Background synchronization manager."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone

from election_platform.logging.setup import get_logger

from app.services.api_client import APIClient, APIClientError
from app.services.local_vote_queue_service import LocalVoteQueueService
from app.sync.node_auth import NodeAuthenticator
from app.sync.queue_manager import QueueManager
from app.sync.sync_logger import SyncLogger
from app.sync.vote_serializer import build_upload_request_from_payloads

logger = get_logger("desktop.sync")


class SyncManager:
    """Background vote synchronization coordinator.

    Workflow: Save Vote → Queue → Upload → ACK → Remove from Queue
    """

    def __init__(
        self,
        api_client: APIClient,
        queue_manager: QueueManager,
        queue_service: LocalVoteQueueService | None = None,
        node_authenticator: NodeAuthenticator | None = None,
        sync_path: str = "/api/v1/sync/votes",
        *,
        node_id: str = "",
        config_version: int = 0,
        batch_size: int = 20,
        poll_interval_seconds: float = 0.2,
        uploads_enabled: bool = True,
        sync_logger: SyncLogger | None = None,
    ) -> None:
        self.api_client = api_client
        self.queue_manager = queue_manager
        self.queue_service = queue_service
        self.node_authenticator = node_authenticator
        self.sync_path = sync_path
        self.node_id = node_id
        self.config_version = config_version
        self.batch_size = batch_size
        self.poll_interval_seconds = poll_interval_seconds
        self.uploads_enabled = uploads_enabled
        self.sync_logger = sync_logger or SyncLogger()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._retry_not_before: dict[str, float] = {}
        self.last_sync_at: str | None = None
        self.last_error: str | None = None
        self.last_success_count = 0
        self.is_online = True

    def start(self) -> None:
        if not self.uploads_enabled:
            logger.info("Vote upload worker disabled")
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker, daemon=True, name="vote-sync")
        self._thread.start()
        logger.info("Background vote synchronization started")

    def stop(self) -> None:
        self._stop_event.set()

    def update_config(self, *, node_id: str | None = None, config_version: int | None = None) -> None:
        """Refresh node identity used for upload payloads."""
        if node_id is not None:
            self.node_id = node_id
        if config_version is not None:
            self.config_version = config_version

    def status(self) -> dict:
        queue_status = (
            self.queue_service.queue_status()
            if self.queue_service is not None
            else {
                "queue_size": self.queue_manager.size(),
                "primary_queue_size": self.queue_manager.primary_size(),
                "retry_queue_size": self.queue_manager.retry_size(),
            }
        )
        return {
            **queue_status,
            "last_sync_at": self.last_sync_at,
            "last_error": self.last_error,
            "last_success_count": self.last_success_count,
            "running": bool(self._thread and self._thread.is_alive()),
            "uploads_enabled": self.uploads_enabled,
            "online": self.is_online,
        }

    def _worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                if self.queue_manager.size() == 0:
                    time.sleep(self.poll_interval_seconds)
                    continue

                if self.queue_service is None:
                    time.sleep(self.poll_interval_seconds)
                    continue

                batch_uuids = self._next_ready_batch()
                if not batch_uuids:
                    time.sleep(1)
                    continue

                self._upload_batch(batch_uuids)
            except Exception as exc:
                self.last_error = str(exc)
                logger.warning("Vote sync error: %s", exc)
                time.sleep(5)

            time.sleep(self.poll_interval_seconds)

    def _next_ready_batch(self) -> list[str]:
        """Select votes that are ready for upload, respecting retry backoff."""
        assert self.queue_service is not None
        candidates = self.queue_manager.peek_batch(self.batch_size)
        ready: list[str] = []
        now = time.monotonic()

        for vote_uuid in candidates:
            retry_count = self.queue_service.get_retry_count(vote_uuid)
            if retry_count == 0:
                ready.append(vote_uuid)
                continue

            not_before = self._retry_not_before.get(vote_uuid, 0.0)
            if now >= not_before:
                ready.append(vote_uuid)

        return ready

    def _upload_batch(self, vote_uuids: list[str]) -> None:
        assert self.queue_service is not None

        for vote_uuid in vote_uuids:
            self.queue_service.mark_uploading(vote_uuid)

        votes = self.queue_service.get_sync_payloads_for_uuids(vote_uuids)
        if not votes:
            return

        if not self.node_id:
            self.last_error = "Node ID is not configured"
            self._schedule_retries(vote_uuids)
            return

        if self.node_authenticator is None or not self.node_authenticator.has_credentials:
            self.last_error = "Node credentials are not configured"
            self._schedule_retries(vote_uuids)
            return

        payload = build_upload_request_from_payloads(
            node_id=self.node_id,
            config_version=self.config_version,
            votes=votes,
        )
        self.sync_logger.upload_started(vote_uuids)

        try:
            headers = self.node_authenticator.auth_headers()
            response = self.api_client.post(self.sync_path, json=payload, headers=headers)
        except APIClientError as exc:
            self._handle_offline(str(exc), vote_uuids)
            self._schedule_retries(vote_uuids)
            return

        if response.status_code == 401:
            self.node_authenticator.invalidate()
            try:
                headers = self.node_authenticator.auth_headers()
                response = self.api_client.post(self.sync_path, json=payload, headers=headers)
            except APIClientError as exc:
                self._handle_offline(str(exc), vote_uuids)
                self._schedule_retries(vote_uuids)
                return

        if response.status_code >= 500 or response.status_code == 408:
            self._handle_offline(f"Server error {response.status_code}", vote_uuids)
            self._schedule_retries(vote_uuids)
            return

        if response.status_code >= 400:
            self.last_error = f"Upload rejected with status {response.status_code}"
            self.sync_logger.upload_failed(self.last_error, vote_uuids=vote_uuids)
            for vote_uuid in vote_uuids:
                self._mark_failed_with_backoff(vote_uuid)
            return

        body = response.json()
        ack = body.get("data") or {}
        accepted = set(ack.get("accepted") or [])
        duplicates = set(ack.get("duplicates") or [])
        failed = set(ack.get("failed") or [])

        success_uuids = accepted | duplicates
        self.is_online = True
        self.last_error = None
        self.last_success_count = len(success_uuids)
        self.last_sync_at = datetime.now(timezone.utc).isoformat()
        self.sync_logger.upload_success(len(accepted), len(duplicates))

        for vote_uuid in success_uuids:
            self.sync_logger.ack_received(vote_uuid)
            self.queue_service.mark_acknowledged(vote_uuid)
            self.sync_logger.queue_removed(vote_uuid)
            self._retry_not_before.pop(vote_uuid, None)
            if vote_uuid in duplicates:
                self.sync_logger.duplicate_ignored(vote_uuid)

        for vote_uuid in failed:
            self._mark_failed_with_backoff(vote_uuid)

        unreported = set(vote_uuids) - success_uuids - failed
        for vote_uuid in unreported:
            self._mark_failed_with_backoff(vote_uuid)

    def _handle_offline(self, message: str, vote_uuids: list[str]) -> None:
        self.is_online = False
        self.last_error = message
        self.sync_logger.upload_failed(message, vote_uuids=vote_uuids)
        self.sync_logger.offline()

    def _schedule_retries(self, vote_uuids: list[str]) -> None:
        for vote_uuid in vote_uuids:
            self._mark_failed_with_backoff(vote_uuid)

    def _mark_failed_with_backoff(self, vote_uuid: str) -> None:
        assert self.queue_service is not None
        retry_count = self.queue_service.mark_failed(vote_uuid)
        backoff = self.queue_service.retry_backoff_seconds(retry_count - 1)
        self._retry_not_before[vote_uuid] = time.monotonic() + backoff
        self.sync_logger.retry_scheduled(vote_uuid, retry_count, backoff)
