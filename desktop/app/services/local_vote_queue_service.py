"""Local vote queue orchestration — persistence first, FakeRedis mirror."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from election_platform.enums.admin import LocalVoteSyncStatus
from election_platform.logging.setup import get_logger

from app.database.session import LocalDatabase, local_db
from app.exceptions import DuplicateVoteError
from app.models.local_vote import LocalVote
from app.models.queue import LocalQueueItem
from app.repositories.local_vote_repository import LocalVoteRepository
from app.repositories.queue_repository import LocalQueueRepository
from app.sync.queue_manager import QueueManager
from app.sync.retry_manager import RetryManager

logger = get_logger("desktop.queue")


@dataclass(frozen=True)
class VoteRecord:
    """Vote payload persisted before enqueue."""

    vote_uuid: str
    election_id: str
    position_id: str
    candidate_id: str
    node_id: str | None
    election_type: str
    house_id: str | None


class LocalVoteQueueService:
    """Coordinate SQLite/MySQL persistence and FakeRedis queue mirroring."""

    def __init__(
        self,
        queue_manager: QueueManager,
        database: LocalDatabase | None = None,
        retry_manager: RetryManager | None = None,
    ) -> None:
        self.queue_manager = queue_manager
        self.database = database or local_db
        self.retry_manager = retry_manager or RetryManager()

    def record_and_enqueue(self, vote: VoteRecord) -> str:
        """Persist a vote, enqueue its UUID, and mirror to FakeRedis.

        Raises DuplicateVoteError if the vote UUID already exists locally.
        """
        if self._vote_exists(vote.vote_uuid):
            raise DuplicateVoteError(f"Vote {vote.vote_uuid} already exists")

        self._persist_vote(vote)
        self._mirror_to_fake_redis(vote.vote_uuid, retry=False)
        logger.info("Vote %s recorded and queued", vote.vote_uuid)
        return vote.vote_uuid

    def mark_uploading(self, vote_uuid: str) -> None:
        """Mark a vote as actively uploading."""
        with self.database.session_scope() as session:
            vote_repo = LocalVoteRepository(session)
            queue_repo = LocalQueueRepository(session)
            local_vote = vote_repo.get_by_vote_uuid(vote_uuid)
            queue_item = queue_repo.get_by_vote_uuid(vote_uuid)
            if local_vote is None or queue_item is None:
                return
            local_vote.sync_status = LocalVoteSyncStatus.UPLOADING.value
            queue_item.queue_status = LocalVoteSyncStatus.UPLOADING.value

    def mark_acknowledged(self, vote_uuid: str) -> None:
        """Remove a vote from queues after backend acknowledgment."""
        with self.database.session_scope() as session:
            vote_repo = LocalVoteRepository(session)
            queue_repo = LocalQueueRepository(session)
            local_vote = vote_repo.get_by_vote_uuid(vote_uuid)
            queue_item = queue_repo.get_by_vote_uuid(vote_uuid)
            if local_vote is not None:
                local_vote.sync_status = LocalVoteSyncStatus.ACKNOWLEDGED.value
            if queue_item is not None:
                queue_repo.delete(queue_item)

        self.queue_manager.acknowledge(vote_uuid)
        logger.info("Vote %s acknowledged and removed from queue", vote_uuid)

    def mark_failed(self, vote_uuid: str) -> int:
        """Increment retry count and move the vote to the retry queue."""
        retry_count = 0
        with self.database.session_scope() as session:
            vote_repo = LocalVoteRepository(session)
            queue_repo = LocalQueueRepository(session)
            local_vote = vote_repo.get_by_vote_uuid(vote_uuid)
            queue_item = queue_repo.get_by_vote_uuid(vote_uuid)
            if local_vote is None or queue_item is None:
                return retry_count

            queue_item.retry_count += 1
            retry_count = queue_item.retry_count
            status = (
                LocalVoteSyncStatus.RETRYING.value
                if self.retry_manager.should_retry(retry_count)
                else LocalVoteSyncStatus.FAILED.value
            )
            local_vote.sync_status = status
            queue_item.queue_status = status

        self.queue_manager.move_to_retry(vote_uuid)
        logger.warning(
            "Vote %s marked for retry (attempt %s, backoff %ss)",
            vote_uuid,
            retry_count,
            self.retry_manager.backoff_seconds(retry_count - 1),
        )
        return retry_count

    def retry_backoff_seconds(self, retry_count: int) -> int:
        return self.retry_manager.backoff_seconds(retry_count)

    def get_sync_payloads_for_uuids(self, vote_uuids: list[str]) -> list[dict]:
        """Load vote upload payloads while the database session is active."""
        if not vote_uuids:
            return []

        from app.sync.vote_serializer import serialize_vote_payload

        with self.database.session_scope() as session:
            vote_repo = LocalVoteRepository(session)
            payloads: list[dict] = []
            for vote_uuid in vote_uuids:
                vote = vote_repo.get_by_vote_uuid(vote_uuid)
                if vote is not None:
                    payloads.append(serialize_vote_payload(vote))
            return payloads

    def get_votes_for_uuids(self, vote_uuids: list[str]) -> list[LocalVote]:
        """Load persisted vote rows for the given UUIDs."""
        if not vote_uuids:
            return []

        with self.database.session_scope() as session:
            vote_repo = LocalVoteRepository(session)
            votes: list[LocalVote] = []
            for vote_uuid in vote_uuids:
                vote = vote_repo.get_by_vote_uuid(vote_uuid)
                if vote is not None:
                    votes.append(vote)
            return votes

    def get_retry_count(self, vote_uuid: str) -> int:
        """Return the current retry count for a queued vote."""
        with self.database.session_scope() as session:
            queue_repo = LocalQueueRepository(session)
            item = queue_repo.get_by_vote_uuid(vote_uuid)
            return item.retry_count if item is not None else 0

    def queue_status(self) -> dict:
        return {
            "queue_size": self.queue_manager.size(),
            "primary_queue_size": self.queue_manager.primary_size(),
            "retry_queue_size": self.queue_manager.retry_size(),
        }

    def get_last_vote_time(self) -> datetime | None:
        """Return when the most recent vote was cast locally."""
        with self.database.session_scope() as session:
            vote_repo = LocalVoteRepository(session)
            return vote_repo.get_latest_created_at()

    def _vote_exists(self, vote_uuid: str) -> bool:
        with self.database.session_scope() as session:
            vote_repo = LocalVoteRepository(session)
            queue_repo = LocalQueueRepository(session)
            return (
                vote_repo.get_by_vote_uuid(vote_uuid) is not None
                or queue_repo.get_by_vote_uuid(vote_uuid) is not None
            )

    def _persist_vote(self, vote: VoteRecord) -> None:
        with self.database.session_scope() as session:
            vote_repo = LocalVoteRepository(session)
            queue_repo = LocalQueueRepository(session)
            vote_repo.add(
                LocalVote(
                    vote_uuid=vote.vote_uuid,
                    election_id=vote.election_id,
                    position_id=vote.position_id,
                    candidate_id=vote.candidate_id,
                    node_id=vote.node_id,
                    election_type=vote.election_type,
                    house_id=vote.house_id,
                    sync_status=LocalVoteSyncStatus.PENDING.value,
                )
            )
            queue_repo.add(
                LocalQueueItem(
                    vote_uuid=vote.vote_uuid,
                    queue_status=LocalVoteSyncStatus.PENDING.value,
                    retry_count=0,
                )
            )

    def _mirror_to_fake_redis(self, vote_uuid: str, *, retry: bool) -> None:
        if retry:
            enqueued = self.queue_manager.enqueue_retry(vote_uuid)
        else:
            enqueued = self.queue_manager.enqueue(vote_uuid)
        if not enqueued and not self.queue_manager.contains(vote_uuid):
            logger.warning("Vote %s persisted but FakeRedis mirror was skipped as duplicate", vote_uuid)
