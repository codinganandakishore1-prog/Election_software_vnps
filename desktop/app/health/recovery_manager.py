"""Automatic queue recovery after crashes or restarts."""

from __future__ import annotations

from dataclasses import dataclass

from election_platform.enums.admin import LocalVoteSyncStatus
from election_platform.logging.setup import get_logger

from app.database.session import LocalDatabase, local_db
from app.models.queue import LocalQueueItem
from app.repositories.local_vote_repository import LocalVoteRepository
from app.repositories.queue_repository import LocalQueueRepository
from app.sync.queue_manager import QueueManager

logger = get_logger("desktop.recovery")


@dataclass(frozen=True)
class RecoveryResult:
    """Summary of queue recovery performed at startup."""

    recovered_votes: int
    primary_count: int
    retry_count: int
    reset_uploading: int


class RecoveryManager:
    """Rebuild FakeRedis queues from persistent local storage."""

    def __init__(
        self,
        queue_manager: QueueManager,
        database: LocalDatabase | None = None,
    ) -> None:
        self.queue_manager = queue_manager
        self.database = database or local_db

    def recover(self) -> RecoveryResult:
        """Restore in-memory queues from SQLite/MySQL after application restart."""
        primary_uuids: list[str] = []
        retry_uuids: list[str] = []
        reset_uploading = 0

        with self.database.session_scope() as session:
            vote_repo = LocalVoteRepository(session)
            queue_repo = LocalQueueRepository(session)

            for vote in vote_repo.list_by_sync_status(LocalVoteSyncStatus.UPLOADING):
                vote.sync_status = LocalVoteSyncStatus.PENDING.value
                reset_uploading += 1

            retryable_items = queue_repo.list_retryable()
            for item in retryable_items:
                if item.queue_status == LocalVoteSyncStatus.UPLOADING.value:
                    item.queue_status = LocalVoteSyncStatus.PENDING.value
                    reset_uploading += 1

            retryable_items.sort(key=lambda item: item.created_at)
            primary_uuids, retry_uuids = self._partition_queue_items(retryable_items)

        recovered = self.queue_manager.rebuild(primary_uuids, retry_uuids)
        result = RecoveryResult(
            recovered_votes=recovered,
            primary_count=len(primary_uuids),
            retry_count=len(retry_uuids),
            reset_uploading=reset_uploading,
        )
        logger.info(
            "Queue recovery complete: %s votes restored (%s primary, %s retry, %s uploading reset)",
            result.recovered_votes,
            result.primary_count,
            result.retry_count,
            result.reset_uploading,
        )
        return result

    @staticmethod
    def _partition_queue_items(
        items: list[LocalQueueItem],
    ) -> tuple[list[str], list[str]]:
        primary_uuids: list[str] = []
        retry_uuids: list[str] = []
        for item in items:
            if item.retry_count > 0:
                retry_uuids.append(item.vote_uuid)
            else:
                primary_uuids.append(item.vote_uuid)
        return primary_uuids, retry_uuids
