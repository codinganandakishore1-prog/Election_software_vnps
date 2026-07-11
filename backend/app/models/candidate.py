"""Candidate ORM models."""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Candidate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Election candidate."""

    __tablename__ = "candidates"

    election_id: Mapped[str] = mapped_column(String(36), ForeignKey("elections.id"), nullable=False)
    position_id: Mapped[str] = mapped_column(String(36), ForeignKey("positions.id"), nullable=False)
    house_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("houses.id"), nullable=True)
    candidate_name: Mapped[str] = mapped_column(String(150), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    image_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("candidate_images.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Draft", nullable=False)


class CandidateImage(Base, UUIDPrimaryKeyMixin):
    """Candidate photograph metadata."""

    __tablename__ = "candidate_images"

    original_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    processed_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    uploaded_at: Mapped[datetime | None] = mapped_column(nullable=True)
    uploaded_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
