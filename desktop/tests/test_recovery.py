"""Recovery workflow tests for desktop vote queue."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.database.session import LocalDatabase
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

    db_path = tmp_path / "recovery_test.db"
    database = LocalDatabase()
    engine = create_engine(
        f"sqlite:///{db_path}",
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )
    database._engine = engine
    database._session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    database.create_tables()
    return database


@pytest.fixture
def queue_manager() -> QueueManager:
    return QueueManager()


@pytest.fixture
def queue_service(queue_manager: QueueManager, temp_db: LocalDatabase) -> LocalVoteQueueService:
    return LocalVoteQueueService(queue_manager, database=temp_db, retry_manager=RetryManager())


def test_recovery_manager_rebuilds_queue_from_storage(
    queue_service: LocalVoteQueueService,
    queue_manager: QueueManager,
    temp_db: LocalDatabase,
) -> None:
    vote = VoteRecord(
        vote_uuid=str(uuid.uuid4()),
        election_id="election-1",
        position_id="position-1",
        candidate_id="candidate-1",
        node_id="node-1",
        election_type="Regular",
        house_id=None,
    )
    queue_service.record_and_enqueue(vote)
    queue_manager.clear()

    recovery = RecoveryManager(queue_manager, database=temp_db)
    result = recovery.recover()
    assert result.recovered_votes >= 1


def test_vote_survives_queue_replay(queue_service: LocalVoteQueueService, temp_db: LocalDatabase) -> None:
    vote_uuid = str(uuid.uuid4())
    vote = VoteRecord(
        vote_uuid=vote_uuid,
        election_id="election-1",
        position_id="position-1",
        candidate_id="candidate-1",
        node_id="node-1",
        election_type="Regular",
        house_id=None,
    )
    queue_service.record_and_enqueue(vote)

    with temp_db.session_scope() as session:
        vote_repo = LocalVoteRepository(session)
        queue_repo = LocalQueueRepository(session)
        assert vote_repo.get_by_vote_uuid(vote_uuid) is not None
        assert queue_repo.get_by_vote_uuid(vote_uuid) is not None
