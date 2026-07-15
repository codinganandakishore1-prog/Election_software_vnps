"""Vote and synchronization ORM models."""

from datetime import datetime
from typing import TYPE_CHECKING

from election_platform.enums.admin import SyncLogStatus
from election_platform.enums.election import ElectionType
from election_platform.enums.sync import QueueStatus
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDPrimaryKeyMixin
from app.database.enums import enum_column

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.election import Election
    from app.models.house import House
    from app.models.node import NodeDownload, VotingNode
    from app.models.position import Position
    from app.models.user import User


class Vote(Base, UUIDPrimaryKeyMixin):
    """Synchronized vote record."""

    __tablename__ = "votes"
    __table_args__ = (
        Index("ix_votes_vote_uuid", "vote_uuid", unique=True),
        Index("ix_votes_candidate_id", "candidate_id"),
        Index("ix_votes_position_id", "position_id"),
        Index("ix_votes_node_id", "node_id"),
        Index("ix_votes_election_id", "election_id"),
        Index("ix_votes_house_id", "house_id"),
        Index("ix_votes_election_id_candidate_id", "election_id", "candidate_id"),
        Index("ix_votes_election_id_position_id", "election_id", "position_id"),
    )

    vote_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    election_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("elections.id", ondelete="RESTRICT"),
        nullable=False,
    )
    position_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("positions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("candidates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("voting_nodes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    election_type: Mapped[ElectionType] = mapped_column(
        enum_column(ElectionType, name="vote_election_type"),
        nullable=False,
    )
    house_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("houses.id", ondelete="RESTRICT"),
        nullable=True,
    )
    voted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    election: Mapped["Election"] = relationship(back_populates="votes")
    position: Mapped["Position"] = relationship(back_populates="votes")
    candidate: Mapped["Candidate"] = relationship(back_populates="votes")
    node: Mapped["VotingNode"] = relationship(back_populates="votes")
    house: Mapped["House | None"] = relationship(back_populates="votes")


class VoteQueue(Base, UUIDPrimaryKeyMixin):
    """Website-side vote queue monitoring."""

    __tablename__ = "vote_queue"
    __table_args__ = (
        Index("ix_vote_queue_node_id", "node_id"),
        Index("ix_vote_queue_queue_status", "queue_status"),
        Index("ix_vote_queue_node_id_queue_status", "node_id", "queue_status"),
    )

    vote_uuid: Mapped[str] = mapped_column(String(36), nullable=False)
    node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("voting_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    received_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    queue_status: Mapped[QueueStatus] = mapped_column(
        enum_column(QueueStatus, name="vote_queue_status"),
        nullable=False,
    )

    node: Mapped["VotingNode"] = relationship(back_populates="vote_queue_items")


class SyncLog(Base, UUIDPrimaryKeyMixin):
    """Synchronization history."""

    __tablename__ = "sync_logs"
    __table_args__ = (Index("ix_sync_logs_node_id", "node_id"),)

    node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("voting_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    sync_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sync_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[SyncLogStatus] = mapped_column(
        enum_column(SyncLogStatus, name="sync_log_status"),
        nullable=False,
    )

    node: Mapped["VotingNode"] = relationship(back_populates="sync_logs")


class PublishedConfiguration(Base, UUIDPrimaryKeyMixin):
    """Published election configuration package."""

    __tablename__ = "published_configurations"
    __table_args__ = (
        Index("ix_published_configurations_election_id", "election_id"),
        Index("ix_published_configurations_version", "version"),
    )

    election_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("elections.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    package_path: Mapped[str] = mapped_column(String(255), nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    election: Mapped["Election"] = relationship(back_populates="published_configurations")
    publisher: Mapped["User | None"] = relationship()
    downloads: Mapped[list["NodeDownload"]] = relationship(back_populates="configuration")
