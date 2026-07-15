"""Election ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING

from election_platform.enums.election import ElectionStatus
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.database.enums import enum_column

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.position import Position
    from app.models.report import Report
    from app.models.sync import PublishedConfiguration, Vote
    from app.models.user import User


class Election(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Election master record."""

    __tablename__ = "elections"
    __table_args__ = (
        Index("ix_elections_status", "status"),
        Index("ix_elections_version", "version"),
        Index("ix_elections_academic_year", "academic_year"),
    )

    election_name: Mapped[str] = mapped_column(String(200), nullable=False)
    academic_year: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[ElectionStatus] = mapped_column(
        enum_column(ElectionStatus, name="election_status"),
        default=ElectionStatus.DRAFT,
        nullable=False,
    )
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    configuration_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    creator: Mapped["User | None"] = relationship(back_populates="elections_created")
    positions: Mapped[list["Position"]] = relationship(
        back_populates="election",
        cascade="all, delete-orphan",
    )
    candidates: Mapped[list["Candidate"]] = relationship(
        back_populates="election",
        cascade="all, delete-orphan",
    )
    votes: Mapped[list["Vote"]] = relationship(back_populates="election")
    reports: Mapped[list["Report"]] = relationship(back_populates="election")
    published_configurations: Mapped[list["PublishedConfiguration"]] = relationship(
        back_populates="election",
    )
