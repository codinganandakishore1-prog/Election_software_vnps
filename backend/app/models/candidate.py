"""Candidate ORM models."""

from datetime import datetime
from typing import TYPE_CHECKING

from election_platform.enums.election import CandidateStatus
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from app.database.enums import enum_column

if TYPE_CHECKING:
    from app.models.election import Election
    from app.models.house import House
    from app.models.position import Position
    from app.models.sync import Vote
    from app.models.user import User


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
    uploaded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=True,
    )
    uploaded_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    uploader: Mapped["User | None"] = relationship()
    candidate: Mapped["Candidate | None"] = relationship(
        back_populates="image",
        uselist=False,
    )


class Candidate(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Election candidate."""

    __tablename__ = "candidates"
    __table_args__ = (
        CheckConstraint("display_order >= 1", name="ck_candidates_display_order_min"),
        Index("ix_candidates_election_id", "election_id"),
        Index("ix_candidates_position_id", "position_id"),
        Index("ix_candidates_house_id", "house_id"),
        Index("ix_candidates_candidate_name", "candidate_name"),
        Index("ix_candidates_status", "status"),
        Index("ix_candidates_display_order", "display_order"),
        Index("ix_candidates_election_id_position_id", "election_id", "position_id"),
        Index("ix_candidates_position_id_display_order", "position_id", "display_order"),
    )

    election_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("elections.id", ondelete="CASCADE"),
        nullable=False,
    )
    position_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=False,
    )
    house_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("houses.id", ondelete="RESTRICT"),
        nullable=True,
    )
    candidate_name: Mapped[str] = mapped_column(String(150), nullable=False)
    candidate_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    candidate_section: Mapped[str | None] = mapped_column(String(50), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    image_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("candidate_images.id", ondelete="RESTRICT"),
        nullable=True,
    )
    status: Mapped[CandidateStatus] = mapped_column(
        enum_column(CandidateStatus, name="candidate_status"),
        default=CandidateStatus.DRAFT,
        nullable=False,
    )

    election: Mapped["Election"] = relationship(back_populates="candidates")
    position: Mapped["Position"] = relationship(back_populates="candidates")
    house: Mapped["House | None"] = relationship(back_populates="candidates")
    image: Mapped["CandidateImage | None"] = relationship(
        back_populates="candidate",
        uselist=False,
    )
    votes: Mapped[list["Vote"]] = relationship(back_populates="candidate")
