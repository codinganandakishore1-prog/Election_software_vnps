"""Desktop queue repository."""

from election_platform.enums.admin import LocalVoteSyncStatus
from sqlalchemy import select

from app.models.queue import LocalQueueItem
from app.repositories.base import LocalBaseRepository


class LocalQueueRepository(LocalBaseRepository[LocalQueueItem]):
    """Data access for persistent sync queue entries."""

    model = LocalQueueItem

    def get_by_vote_uuid(self, vote_uuid: str) -> LocalQueueItem | None:
        return self.get_by_field("vote_uuid", vote_uuid)

    def list_pending(self) -> list[LocalQueueItem]:
        stmt = select(LocalQueueItem).where(
            LocalQueueItem.queue_status == LocalVoteSyncStatus.PENDING.value
        )
        return list(self.db.scalars(stmt).all())

    def list_retryable(self) -> list[LocalQueueItem]:
        stmt = select(LocalQueueItem).where(
            LocalQueueItem.queue_status.in_(
                [
                    LocalVoteSyncStatus.PENDING.value,
                    LocalVoteSyncStatus.UPLOADING.value,
                    LocalVoteSyncStatus.RETRYING.value,
                    LocalVoteSyncStatus.FAILED.value,
                ]
            )
        )
        return list(self.db.scalars(stmt).all())

    def list_by_status(self, queue_status: LocalVoteSyncStatus) -> list[LocalQueueItem]:
        return self.list_by_field("queue_status", queue_status.value)
