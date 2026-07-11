"""Vote and synchronization ORM models."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin


class Vote(Base, UUIDPrimaryKeyMixin):
    """Synchronized vote record."""

    __tablename__ = "votes"

    vote_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    election_id: Mapped[str] = mapped_column(String(36), ForeignKey("elections.id"), nullable=False)
    position_id: Mapped[str] = mapped_column(String(36), ForeignKey("positions.id"), nullable=False)
    candidate_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidates.id"), nullable=False)
    node_id: Mapped[str] = mapped_column(String(36), ForeignKey("voting_nodes.id"), nullable=False)
    election_type: Mapped[str] = mapped_column(String(20), nullable=False)
    house_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("houses.id"), nullable=True)
    voted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class VoteQueue(Base, UUIDPrimaryKeyMixin):
    """Website-side vote queue monitoring."""

    __tablename__ = "vote_queue"

    vote_uuid: Mapped[str] = mapped_column(String(36), nullable=False)
    node_id: Mapped[str] = mapped_column(String(36), ForeignKey("voting_nodes.id"), nullable=False)
    received_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    queue_status: Mapped[str] = mapped_column(String(20), nullable=False)


class SyncLog(Base, UUIDPrimaryKeyMixin):
    """Synchronization history."""

    __tablename__ = "sync_logs"

    node_id: Mapped[str] = mapped_column(String(36), ForeignKey("voting_nodes.id"), nullable=False)
    sync_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sync_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class PublishedConfiguration(Base, UUIDPrimaryKeyMixin):
    """Published election configuration package."""

    __tablename__ = "published_configurations"

    election_id: Mapped[str] = mapped_column(String(36), ForeignKey("elections.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    package_path: Mapped[str] = mapped_column(String(255), nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
