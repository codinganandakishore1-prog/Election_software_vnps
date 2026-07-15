"""Voting node ORM models."""

from datetime import datetime
from typing import TYPE_CHECKING

from election_platform.enums.admin import InstallStatus, SessionStatus
from election_platform.enums.election import ElectionType
from election_platform.enums.sync import SyncStatus
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.database.enums import enum_column

if TYPE_CHECKING:
    from app.models.house import House
    from app.models.sync import PublishedConfiguration, SyncLog, Vote, VoteQueue


class VotingNode(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Registered voting machine."""

    __tablename__ = "voting_nodes"
    __table_args__ = (
        Index("ix_voting_nodes_house_id", "house_id"),
        Index("ix_voting_nodes_config_version", "config_version"),
        Index("ix_voting_nodes_election_type_active", "election_type", "active"),
    )

    node_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    node_secret: Mapped[str] = mapped_column(String(255), nullable=False)
    election_type: Mapped[ElectionType] = mapped_column(
        enum_column(ElectionType, name="node_election_type"),
        nullable=False,
    )
    house_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("houses.id", ondelete="RESTRICT"),
        nullable=True,
    )
    app_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    config_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    house: Mapped["House | None"] = relationship(back_populates="voting_nodes")
    heartbeats: Mapped[list["NodeHeartbeat"]] = relationship(back_populates="node")
    sessions: Mapped[list["NodeSession"]] = relationship(back_populates="node")
    downloads: Mapped[list["NodeDownload"]] = relationship(back_populates="node")
    sync_logs: Mapped[list["SyncLog"]] = relationship(back_populates="node")
    votes: Mapped[list["Vote"]] = relationship(back_populates="node")
    vote_queue_items: Mapped[list["VoteQueue"]] = relationship(back_populates="node")


class NodeHeartbeat(Base, UUIDPrimaryKeyMixin):
    """Node heartbeat history."""

    __tablename__ = "node_heartbeats"
    __table_args__ = (
        Index("ix_node_heartbeats_node_id", "node_id"),
        Index("ix_node_heartbeats_heartbeat_time", "heartbeat_time"),
        Index("ix_node_heartbeats_node_id_heartbeat_time", "node_id", "heartbeat_time"),
    )

    node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("voting_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    heartbeat_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    queue_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_vote_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_status: Mapped[SyncStatus] = mapped_column(
        enum_column(SyncStatus, name="heartbeat_sync_status"),
        nullable=False,
    )
    app_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    config_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)

    node: Mapped[VotingNode] = relationship(back_populates="heartbeats")


class NodeSession(Base, UUIDPrimaryKeyMixin):
    """Authenticated desktop node session."""

    __tablename__ = "node_sessions"
    __table_args__ = (Index("ix_node_sessions_node_id", "node_id"),)

    node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("voting_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    login_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    logout_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    jwt_token_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    session_status: Mapped[SessionStatus] = mapped_column(
        enum_column(SessionStatus, name="node_session_status"),
        nullable=False,
    )

    node: Mapped[VotingNode] = relationship(back_populates="sessions")


class NodeDownload(Base, UUIDPrimaryKeyMixin):
    """Configuration download history."""

    __tablename__ = "node_downloads"
    __table_args__ = (Index("ix_node_downloads_node_id", "node_id"),)

    node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("voting_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    configuration_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("published_configurations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    download_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    install_status: Mapped[InstallStatus] = mapped_column(
        enum_column(InstallStatus, name="node_install_status"),
        nullable=False,
    )

    node: Mapped[VotingNode] = relationship(back_populates="downloads")
    configuration: Mapped["PublishedConfiguration"] = relationship(back_populates="downloads")
