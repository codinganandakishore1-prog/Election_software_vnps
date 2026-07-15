"""Desktop local vote ORM model."""

from datetime import datetime

from election_platform.enums.admin import LocalVoteSyncStatus
from election_platform.enums.election import ElectionType
from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import LocalBase, utc_now


class LocalVote(LocalBase):
    """Persistent local vote storage before synchronization."""

    __tablename__ = "local_votes"
    __table_args__ = (
        Index("ix_local_votes_sync_status", "sync_status"),
        Index("ix_local_votes_election_id", "election_id"),
        Index("ix_local_votes_created_at", "created_at"),
    )

    vote_uuid: Mapped[str] = mapped_column(String(36), primary_key=True)
    election_id: Mapped[str] = mapped_column(String(36), nullable=False)
    position_id: Mapped[str] = mapped_column(String(36), nullable=False)
    candidate_id: Mapped[str] = mapped_column(String(36), nullable=False)
    node_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    election_type: Mapped[str] = mapped_column(
        String(20),
        default=ElectionType.REGULAR.value,
        nullable=False,
    )
    house_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    sync_status: Mapped[str] = mapped_column(
        String(20),
        default=LocalVoteSyncStatus.PENDING.value,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
