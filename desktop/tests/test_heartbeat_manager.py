"""Tests for the desktop heartbeat manager."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.database.session import LocalDatabase
from app.health.heartbeat_manager import HeartbeatManager
from app.services.api_client import APIClient, APIClientError
from app.services.local_vote_queue_service import LocalVoteQueueService, VoteRecord
from app.sync.node_auth import NodeAuthenticator
from app.sync.queue_manager import QueueManager
from app.sync.retry_manager import RetryManager
from app.sync.sync_manager import SyncManager


@pytest.fixture
def temp_db(tmp_path):
    from pathlib import Path
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    db_path = Path(tmp_path) / "test_heartbeat.db"
    database = LocalDatabase()
    engine = create_engine(
        f"sqlite:///{db_path}",
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )
    database._engine = engine
    database._session_factory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )
    database.create_tables()
    return database


@pytest.fixture
def queue_manager() -> QueueManager:
    return QueueManager()


@pytest.fixture
def queue_service(queue_manager: QueueManager, temp_db: LocalDatabase) -> LocalVoteQueueService:
    return LocalVoteQueueService(queue_manager, database=temp_db, retry_manager=RetryManager())


@pytest.fixture
def sync_manager(queue_service: LocalVoteQueueService, queue_manager: QueueManager) -> SyncManager:
    api_client = MagicMock(spec=APIClient)
    authenticator = MagicMock(spec=NodeAuthenticator)
    authenticator.has_credentials = True
    authenticator.auth_headers.return_value = {"Authorization": "Bearer token"}
    return SyncManager(
        api_client,
        queue_manager,
        queue_service=queue_service,
        node_authenticator=authenticator,
        node_id="node-1",
        config_version=3,
        uploads_enabled=False,
    )


def _enqueue_vote(queue_service: LocalVoteQueueService, vote_uuid: str) -> None:
    queue_service.record_and_enqueue(
        VoteRecord(
            vote_uuid=vote_uuid,
            election_id="election-1",
            position_id="position-1",
            candidate_id="candidate-1",
            node_id="node-1",
            election_type="Regular",
            house_id=None,
        )
    )


def test_heartbeat_sends_status_payload(
    queue_service: LocalVoteQueueService,
    sync_manager: SyncManager,
) -> None:
    vote_uuid = str(uuid.uuid4())
    _enqueue_vote(queue_service, vote_uuid)

    api_client = MagicMock(spec=APIClient)
    response = MagicMock()
    response.status_code = 200
    api_client.post.return_value = response

    authenticator = MagicMock(spec=NodeAuthenticator)
    authenticator.has_credentials = True
    authenticator.auth_headers.return_value = {"Authorization": "Bearer token"}

    manager = HeartbeatManager(
        api_client,
        authenticator,
        queue_service,
        sync_manager,
        node_id="node-1",
        config_version=5,
        interval_seconds=10,
    )

    assert manager._send_heartbeat() is True

    api_client.post.assert_called_once()
    payload = api_client.post.call_args.kwargs["json"]
    assert payload["node_id"] == "node-1"
    assert payload["config_version"] == 5
    assert payload["queue_size"] == 1
    assert payload["last_vote_time"] is not None
    assert payload["sync_status"] == "Syncing"
    assert manager.is_online is True
    assert manager.last_error is None


def test_heartbeat_retries_after_network_error(
    queue_service: LocalVoteQueueService,
    sync_manager: SyncManager,
) -> None:
    api_client = MagicMock(spec=APIClient)
    api_client.post.side_effect = APIClientError("Network error")

    authenticator = MagicMock(spec=NodeAuthenticator)
    authenticator.has_credentials = True
    authenticator.auth_headers.return_value = {"Authorization": "Bearer token"}

    manager = HeartbeatManager(
        api_client,
        authenticator,
        queue_service,
        sync_manager,
        node_id="node-1",
        config_version=1,
        interval_seconds=10,
    )

    assert manager._send_heartbeat() is False
    assert manager.is_online is False
    assert manager.last_error == "Network error"


def test_heartbeat_reauthenticates_on_401(
    queue_service: LocalVoteQueueService,
    sync_manager: SyncManager,
) -> None:
    api_client = MagicMock(spec=APIClient)
    unauthorized = MagicMock()
    unauthorized.status_code = 401
    success = MagicMock()
    success.status_code = 200
    api_client.post.side_effect = [unauthorized, success]

    authenticator = MagicMock(spec=NodeAuthenticator)
    authenticator.has_credentials = True
    authenticator.auth_headers.return_value = {"Authorization": "Bearer token"}

    manager = HeartbeatManager(
        api_client,
        authenticator,
        queue_service,
        sync_manager,
        node_id="node-1",
        config_version=1,
        interval_seconds=10,
    )

    assert manager._send_heartbeat() is True
    authenticator.invalidate.assert_called_once()
    assert api_client.post.call_count == 2


def test_heartbeat_worker_uses_backoff_after_failure(
    queue_service: LocalVoteQueueService,
    sync_manager: SyncManager,
) -> None:
    api_client = MagicMock(spec=APIClient)

    authenticator = MagicMock(spec=NodeAuthenticator)
    authenticator.has_credentials = True
    authenticator.auth_headers.return_value = {"Authorization": "Bearer token"}

    manager = HeartbeatManager(
        api_client,
        authenticator,
        queue_service,
        sync_manager,
        node_id="node-1",
        config_version=1,
        interval_seconds=10,
    )

    with patch.object(manager, "_send_heartbeat", return_value=False) as send_mock:
        with patch.object(manager._stop_event, "wait", return_value=True) as wait_mock:
            manager._worker()

    send_mock.assert_called_once()
    wait_mock.assert_called_once_with(5.0)


def test_get_last_vote_time_returns_latest_vote(
    queue_service: LocalVoteQueueService,
) -> None:
    first_uuid = str(uuid.uuid4())
    second_uuid = str(uuid.uuid4())
    _enqueue_vote(queue_service, first_uuid)
    _enqueue_vote(queue_service, second_uuid)

    last_vote_time = queue_service.get_last_vote_time()
    assert last_vote_time is not None
