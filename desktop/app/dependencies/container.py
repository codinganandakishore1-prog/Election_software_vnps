"""Desktop service container."""

import os
from pathlib import Path

from app.config.settings import settings
from app.data.election_store import ElectionStore
from app.database.init_db import initialize_local_database
from app.health.diagnostics import DiagnosticsService
from app.health.heartbeat_manager import HeartbeatManager
from app.health.recovery_manager import RecoveryManager
from app.runtime_paths import data_root, resource_root
from app.services.api_client import APIClient
from app.services.config_service import ConfigService
from app.services.local_vote_queue_service import LocalVoteQueueService
from app.services.vote_service import VoteService
from app.sync.node_auth import NodeAuthenticator
from app.sync.queue_manager import QueueManager
from app.sync.retry_manager import RetryManager
from app.sync.sync_manager import SyncManager

# Bundled assets root (source tree or PyInstaller _MEIPASS).
DESKTOP_ROOT = resource_root()


def _resolve_data_dir() -> Path:
    """Allow multiple node instances via DESKTOP_DATA_DIR."""
    override = (os.environ.get("DESKTOP_DATA_DIR") or "").strip()
    if override:
        path = Path(override).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path
    return data_root() / "data"


class DesktopContainer:
    """Dependency container for the desktop voting application."""

    def __init__(self, website_url: str | None = None) -> None:
        initialize_local_database()

        self.store = ElectionStore(base_dir=resource_root(), data_dir=_resolve_data_dir())
        resolved_url = website_url or self.store.data.get("website_url") or settings.website_url
        self.api_client = APIClient(base_url=resolved_url)
        self.queue_manager = QueueManager()
        self.retry_manager = RetryManager()
        self.queue_service = LocalVoteQueueService(self.queue_manager, retry_manager=self.retry_manager)
        self.recovery_manager = RecoveryManager(self.queue_manager)
        self.recovery_manager.recover()

        node_id = self.store.data.get("node_id") or settings.node_id
        node_secret = self.store.data.get("node_secret") or settings.node_secret
        config_version = int(self.store.data.get("election_version") or 0)
        self.node_authenticator = NodeAuthenticator(
            self.api_client,
            node_id=node_id,
            node_secret=node_secret,
        )
        self.config_service = ConfigService(
            self.api_client,
            self.store,
            node_authenticator=self.node_authenticator,
        )
        self.vote_service = VoteService(self.store, self.queue_service)
        self.sync_manager = SyncManager(
            self.api_client,
            self.queue_manager,
            queue_service=self.queue_service,
            node_authenticator=self.node_authenticator,
            node_id=node_id,
            config_version=config_version,
            batch_size=settings.sync_batch_size,
            poll_interval_seconds=settings.sync_poll_interval_ms / 1000,
            uploads_enabled=settings.sync_uploads_enabled,
        )
        self.heartbeat_manager = HeartbeatManager(
            self.api_client,
            self.node_authenticator,
            self.queue_service,
            self.sync_manager,
            node_id=node_id,
            config_version=config_version,
        )
        self.diagnostics_service = DiagnosticsService(
            self.store,
            self.sync_manager,
            self.heartbeat_manager,
            resolved_url,
        )


def get_desktop_container(website_url: str | None = None) -> DesktopContainer:
    return DesktopContainer(website_url=website_url)
