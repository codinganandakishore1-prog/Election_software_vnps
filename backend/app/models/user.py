"""User and role ORM models."""

from datetime import datetime
from typing import TYPE_CHECKING

from election_platform.enums.admin import LoginStatus
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from app.database.enums import enum_column

if TYPE_CHECKING:
    from app.models.session import UserSession
    from app.models.audit_log import AuditLog
    from app.models.backup import Backup
    from app.models.election import Election
    from app.models.notification import Notification
    from app.models.report import Report, ReportDownload
    from app.models.settings import MySQLSettings


class Role(Base, UUIDPrimaryKeyMixin):
    """System role."""

    __tablename__ = "roles"

    role_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Administrator and viewer accounts."""

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_role_id", "role_id"),
        Index("ix_users_username", "username"),
        Index("ix_users_email", "email"),
    )

    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    role: Mapped[Role] = relationship(back_populates="users")
    elections_created: Mapped[list["Election"]] = relationship(back_populates="creator")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")
    login_history: Mapped[list["LoginHistory"]] = relationship(back_populates="user")
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")
    reports_generated: Mapped[list["Report"]] = relationship(back_populates="generator")
    report_downloads: Mapped[list["ReportDownload"]] = relationship(back_populates="downloader")
    backups_created: Mapped[list["Backup"]] = relationship(back_populates="creator")
    mysql_settings_updates: Mapped[list["MySQLSettings"]] = relationship(back_populates="updater")


class LoginHistory(Base, UUIDPrimaryKeyMixin):
    """Login activity history."""

    __tablename__ = "login_history"
    __table_args__ = (
        Index("ix_login_history_user_id", "user_id"),
        Index("ix_login_history_login_status", "login_status"),
        Index("ix_login_history_user_id_created", "user_id", "login_time"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    login_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    logout_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(150), nullable=True)
    login_status: Mapped[LoginStatus] = mapped_column(
        enum_column(LoginStatus, name="login_status"),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="login_history")
