"""Local ORM models (placeholder)."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class LocalBase(DeclarativeBase):
    pass


class LocalVote(LocalBase):
    """Local vote storage."""

    __tablename__ = "local_votes"

    vote_uuid: Mapped[str] = mapped_column(String(36), primary_key=True)
    election_id: Mapped[str] = mapped_column(String(36), nullable=False)
    position_id: Mapped[str] = mapped_column(String(36), nullable=False)
    candidate_id: Mapped[str] = mapped_column(String(36), nullable=False)
    sync_status: Mapped[str] = mapped_column(String(20), default="Pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
