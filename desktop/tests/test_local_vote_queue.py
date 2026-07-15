"""Tests for the desktop local vote queue."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.database.session import LocalDatabase
from app.exceptions import DuplicateVoteError
from app.health.recovery_manager import RecoveryManager
from app.repositories.local_vote_repository import LocalVoteRepository
from app.repositories.queue_repository import LocalQueueRepository
from app.services.local_vote_queue_service import LocalVoteQueueService, VoteRecord
from app.sync.queue_manager import QueueManager
from app.sync.retry_manager import RetryManager


@pytest.fixture
def temp_db(tmp_path: Path) -> LocalDatabase:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    db_path = tmp_path / "test_local.db"
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


def _sample_vote(**overrides: object) -> VoteRecord:
    vote_uuid = str(overrides.pop("vote_uuid", uuid.uuid4()))
    return VoteRecord(
        vote_uuid=vote_uuid,
        election_id=str(overrides.get("election_id", "election-1")),
        position_id=str(overrides.get("position_id", "position-1")),
        candidate_id=str(overrides.get("candidate_id", "candidate-1")),
        node_id=overrides.get("node_id", "node-1"),  # type: ignore[arg-type]
        election_type=str(overrides.get("election_type", "Regular")),
        house_id=overrides.get("house_id"),  # type: ignore[arg-type]
    )


def test_record_and_enqueue_persists_and_mirrors(
    queue_service: LocalVoteQueueService,
    queue_manager: QueueManager,
    temp_db: LocalDatabase,
) -> None:
    vote = _sample_vote()
    queue_service.record_and_enqueue(vote)

    assert queue_manager.size() == 1
    assert queue_manager.peek() == vote.vote_uuid

    with temp_db.session_scope() as session:
        vote_repo = LocalVoteRepository(session)
        queue_repo = LocalQueueRepository(session)
        assert vote_repo.get_by_vote_uuid(vote.vote_uuid) is not None
        assert queue_repo.get_by_vote_uuid(vote.vote_uuid) is not None


def test_duplicate_vote_is_rejected(
    queue_service: LocalVoteQueueService,
    queue_manager: QueueManager,
) -> None:
    vote = _sample_vote()
    queue_service.record_and_enqueue(vote)

    with pytest.raises(DuplicateVoteError):
        queue_service.record_and_enqueue(vote)

    assert queue_manager.size() == 1


def test_fake_redis_duplicate_enqueue_is_ignored(queue_manager: QueueManager) -> None:
    vote_uuid = str(uuid.uuid4())
    assert queue_manager.enqueue(vote_uuid) is True
    assert queue_manager.enqueue(vote_uuid) is False
    assert queue_manager.size() == 1


def test_mark_failed_moves_vote_to_retry_queue(
    queue_service: LocalVoteQueueService,
    queue_manager: QueueManager,
    temp_db: LocalDatabase,
) -> None:
    vote = _sample_vote()
    queue_service.record_and_enqueue(vote)

    retry_count = queue_service.mark_failed(vote.vote_uuid)

    assert retry_count == 1
    assert queue_manager.primary_size() == 0
    assert queue_manager.retry_size() == 1

    with temp_db.session_scope() as session:
        queue_repo = LocalQueueRepository(session)
        item = queue_repo.get_by_vote_uuid(vote.vote_uuid)
        assert item is not None
        assert item.retry_count == 1


def test_recovery_rebuilds_fake_redis_after_restart(
    queue_service: LocalVoteQueueService,
    temp_db: LocalDatabase,
) -> None:
    primary_vote = _sample_vote()
    retry_vote = _sample_vote()
    queue_service.record_and_enqueue(primary_vote)
    queue_service.record_and_enqueue(retry_vote)
    queue_service.mark_failed(retry_vote.vote_uuid)

    new_queue_manager = QueueManager()
    recovery = RecoveryManager(new_queue_manager, database=temp_db)
    result = recovery.recover()

    assert result.recovered_votes == 2
    assert result.primary_count == 1
    assert result.retry_count == 1
    assert new_queue_manager.primary_size() == 1
    assert new_queue_manager.retry_size() == 1


def test_retry_backoff_schedule() -> None:
    retry_manager = RetryManager()
    assert retry_manager.backoff_seconds(0) == 5
    assert retry_manager.backoff_seconds(1) == 10
    assert retry_manager.backoff_seconds(4) == 60
    assert retry_manager.backoff_seconds(99) == 60


def test_acknowledge_removes_vote_from_queues(
    queue_service: LocalVoteQueueService,
    queue_manager: QueueManager,
    temp_db: LocalDatabase,
) -> None:
    vote = _sample_vote()
    queue_service.record_and_enqueue(vote)
    queue_service.mark_acknowledged(vote.vote_uuid)

    assert queue_manager.size() == 0
    with temp_db.session_scope() as session:
        queue_repo = LocalQueueRepository(session)
        assert queue_repo.get_by_vote_uuid(vote.vote_uuid) is None
