"""Voting node ORM models."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class VotingNode(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Registered voting machine."""

    __tablename__ = "voting_nodes"

    node_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    node_secret: Mapped[str] = mapped_column(String(255), nullable=False)
    election_type: Mapped[str] = mapped_column(String(20), nullable=False)
    house_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("houses.id"), nullable=True)
    app_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    config_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class NodeHeartbeat(Base, UUIDPrimaryKeyMixin):
    """Node heartbeat history."""

    __tablename__ = "node_heartbeats"

    node_id: Mapped[str] = mapped_column(String(36), ForeignKey("voting_nodes.id"), nullable=False)
    heartbeat_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    queue_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_vote_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(20), nullable=False)
    app_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    config_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)


class NodeSession(Base, UUIDPrimaryKeyMixin):
    """Authenticated desktop node session."""

    __tablename__ = "node_sessions"

    node_id: Mapped[str] = mapped_column(String(36), ForeignKey("voting_nodes.id"), nullable=False)
    login_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    logout_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    jwt_token_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    session_status: Mapped[str] = mapped_column(String(20), nullable=False)


class NodeDownload(Base, UUIDPrimaryKeyMixin):
    """Configuration download history."""

    __tablename__ = "node_downloads"

    node_id: Mapped[str] = mapped_column(String(36), ForeignKey("voting_nodes.id"), nullable=False)
    configuration_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("published_configurations.id"), nullable=False
    )
    download_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    install_status: Mapped[str] = mapped_column(String(20), nullable=False)
