"""Report ORM models."""

from datetime import datetime
from typing import TYPE_CHECKING

from election_platform.enums.admin import ReportType
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.database.enums import enum_column

if TYPE_CHECKING:
    from app.models.election import Election
    from app.models.user import User


class Report(Base, UUIDPrimaryKeyMixin, SoftDeleteMixin):
    """Generated report metadata."""

    __tablename__ = "reports"
    __table_args__ = (
        Index("ix_reports_election_id", "election_id"),
        Index("ix_reports_generated_at", "generated_at"),
        Index("ix_reports_report_type", "report_type"),
        Index("ix_reports_election_id_report_type", "election_id", "report_type"),
    )

    election_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("elections.id", ondelete="RESTRICT"),
        nullable=False,
    )
    report_name: Mapped[str] = mapped_column(String(200), nullable=False)
    report_type: Mapped[ReportType] = mapped_column(
        enum_column(ReportType, name="report_type"),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    generated_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    election: Mapped["Election"] = relationship(back_populates="reports")
    generator: Mapped["User | None"] = relationship(back_populates="reports_generated")
    downloads: Mapped[list["ReportDownload"]] = relationship(back_populates="report")


class ReportDownload(Base, UUIDPrimaryKeyMixin):
    """Report download audit."""

    __tablename__ = "report_downloads"
    __table_args__ = (Index("ix_report_downloads_report_id", "report_id"),)

    report_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    downloaded_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    downloaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)

    report: Mapped[Report] = relationship(back_populates="downloads")
    downloader: Mapped["User | None"] = relationship(back_populates="report_downloads")


class ReportTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Report layout template."""

    __tablename__ = "report_templates"
    __table_args__ = (Index("ix_report_templates_report_type", "report_type"),)

    template_name: Mapped[str] = mapped_column(String(150), nullable=False)
    report_type: Mapped[ReportType] = mapped_column(
        enum_column(ReportType, name="report_template_type"),
        nullable=False,
    )
