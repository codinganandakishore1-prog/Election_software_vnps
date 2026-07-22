"""Desktop local vote repository."""

from datetime import datetime

from election_platform.enums.admin import LocalVoteSyncStatus
from sqlalchemy import select

from app.models.local_vote import LocalVote
from app.repositories.base import LocalBaseRepository


class LocalVoteRepository(LocalBaseRepository[LocalVote]):
    """Data access for local vote records."""

    model = LocalVote

    def get_by_vote_uuid(self, vote_uuid: str) -> LocalVote | None:
        return self.get_by_id(vote_uuid)

    def get_latest_created_at(self) -> datetime | None:
        """Return the timestamp of the most recently cast local vote."""
        stmt = select(LocalVote).order_by(LocalVote.created_at.desc()).limit(1)
        vote = self.db.scalars(stmt).first()
        return vote.created_at if vote is not None else None

    def exists(self, vote_uuid: str) -> bool:
        return self.get_by_vote_uuid(vote_uuid) is not None

    def list_pending(self) -> list[LocalVote]:
        stmt = select(LocalVote).where(
            LocalVote.sync_status == LocalVoteSyncStatus.PENDING.value
        )
        return list(self.db.scalars(stmt).all())

    def list_by_sync_status(self, sync_status: LocalVoteSyncStatus) -> list[LocalVote]:
        return self.list_by_field("sync_status", sync_status.value)
