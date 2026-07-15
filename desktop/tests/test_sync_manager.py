"""Tests for the desktop synchronization manager."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.database.session import LocalDatabase
from app.models.local_vote import LocalVote
from app.services.api_client import APIClient
from app.services.local_vote_queue_service import LocalVoteQueueService, VoteRecord
from app.sync.node_auth import NodeAuthenticator
from app.sync.queue_manager import QueueManager
from app.sync.retry_manager import RetryManager
from app.sync.sync_manager import SyncManager


@pytest.fixture
def temp_db(tmp_path: Path) -> LocalDatabase:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    db_path = tmp_path / "test_sync.db"
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


def test_sync_manager_acknowledges_accepted_votes(
    queue_service: LocalVoteQueueService,
    queue_manager: QueueManager,
) -> None:
    vote_uuid = str(uuid.uuid4())
    _enqueue_vote(queue_service, vote_uuid)

    api_client = MagicMock(spec=APIClient)
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "data": {
            "accepted": [vote_uuid],
            "duplicates": [],
            "failed": [],
        },
    }
    api_client.post.return_value = response

    authenticator = MagicMock(spec=NodeAuthenticator)
    authenticator.has_credentials = True
    authenticator.auth_headers.return_value = {"Authorization": "Bearer token"}

    manager = SyncManager(
        api_client,
        queue_manager,
        queue_service=queue_service,
        node_authenticator=authenticator,
        node_id="node-1",
        config_version=5,
        uploads_enabled=True,
    )

    manager._upload_batch([vote_uuid])

    assert queue_manager.size() == 0
    assert manager.last_success_count == 1
    assert manager.is_online is True


def test_sync_manager_treats_duplicates_as_success(
    queue_service: LocalVoteQueueService,
    queue_manager: QueueManager,
) -> None:
    vote_uuid = str(uuid.uuid4())
    _enqueue_vote(queue_service, vote_uuid)

    api_client = MagicMock(spec=APIClient)
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "data": {
            "accepted": [],
            "duplicates": [vote_uuid],
            "failed": [],
        },
    }
    api_client.post.return_value = response

    authenticator = MagicMock(spec=NodeAuthenticator)
    authenticator.has_credentials = True
    authenticator.auth_headers.return_value = {"Authorization": "Bearer token"}

    manager = SyncManager(
        api_client,
        queue_manager,
        queue_service=queue_service,
        node_authenticator=authenticator,
        node_id="node-1",
        config_version=5,
        uploads_enabled=True,
    )

    manager._upload_batch([vote_uuid])

    assert queue_manager.size() == 0


def test_sync_manager_schedules_retry_on_network_error(
    queue_service: LocalVoteQueueService,
    queue_manager: QueueManager,
) -> None:
    vote_uuid = str(uuid.uuid4())
    _enqueue_vote(queue_service, vote_uuid)

    api_client = MagicMock(spec=APIClient)
    from app.services.api_client import APIClientError

    api_client.post.side_effect = APIClientError("Network error")

    authenticator = MagicMock(spec=NodeAuthenticator)
    authenticator.has_credentials = True
    authenticator.auth_headers.return_value = {"Authorization": "Bearer token"}

    manager = SyncManager(
        api_client,
        queue_manager,
        queue_service=queue_service,
        node_authenticator=authenticator,
        node_id="node-1",
        config_version=5,
        uploads_enabled=True,
    )

    manager._upload_batch([vote_uuid])

    assert queue_manager.retry_size() == 1
    assert manager.is_online is False
    assert vote_uuid in manager._retry_not_before


def test_peek_batch_returns_multiple_votes(queue_manager: QueueManager) -> None:
    uuids = [str(uuid.uuid4()) for _ in range(3)]
    for vote_uuid in uuids:
        queue_manager.enqueue(vote_uuid)

    assert queue_manager.peek_batch(2) == uuids[:2]
    assert queue_manager.size() == 3
