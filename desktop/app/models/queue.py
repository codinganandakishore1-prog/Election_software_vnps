"""Desktop persistent sync queue ORM model."""

from datetime import datetime

from election_platform.enums.admin import LocalVoteSyncStatus
from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import LocalBase, UUIDPrimaryKeyMixin, utc_now


class LocalQueueItem(LocalBase, UUIDPrimaryKeyMixin):
    """Persistent queue entry mirrored to FakeRedis for recovery."""

    __tablename__ = "queue"
    __table_args__ = (
        Index("ix_queue_vote_uuid", "vote_uuid", unique=True),
        Index("ix_queue_queue_status", "queue_status"),
        Index("ix_queue_created_at", "created_at"),
    )

    vote_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    queue_status: Mapped[str] = mapped_column(
        String(20),
        default=LocalVoteSyncStatus.PENDING.value,
        nullable=False,
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
