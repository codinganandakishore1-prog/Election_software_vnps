"""Backup ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING

from election_platform.enums.admin import BackupStatus, BackupType
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDPrimaryKeyMixin, utc_now
from app.database.enums import enum_column

if TYPE_CHECKING:
    from app.models.user import User


class Backup(Base, UUIDPrimaryKeyMixin):
    """System backup record."""

    __tablename__ = "backups"
    __table_args__ = (
        Index("ix_backups_backup_type", "backup_type"),
        Index("ix_backups_created_at", "created_at"),
        Index("ix_backups_status", "status"),
    )

    backup_type: Mapped[BackupType] = mapped_column(
        enum_column(BackupType, name="backup_type"),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    backup_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    status: Mapped[BackupStatus] = mapped_column(
        enum_column(BackupStatus, name="backup_status"),
        nullable=False,
    )

    creator: Mapped["User | None"] = relationship(back_populates="backups_created")
