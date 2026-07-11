"""Report ORM models."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin


class Report(Base, UUIDPrimaryKeyMixin):
    """Generated report metadata."""

    __tablename__ = "reports"

    election_id: Mapped[str] = mapped_column(String(36), ForeignKey("elections.id"), nullable=False)
    report_name: Mapped[str] = mapped_column(String(200), nullable=False)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    generated_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class ReportDownload(Base, UUIDPrimaryKeyMixin):
    """Report download audit."""

    __tablename__ = "report_downloads"

    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("reports.id"), nullable=False)
    downloaded_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    downloaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
