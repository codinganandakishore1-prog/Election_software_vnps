"""Settings and audit ORM models."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SystemSettings(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Website-wide settings."""

    __tablename__ = "system_settings"

    school_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    school_logo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    election_logo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    secondary_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class MySQLSettings(Base, UUIDPrimaryKeyMixin):
    """Website MySQL connection settings."""

    __tablename__ = "mysql_settings"

    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=3306, nullable=False)
    database_name: Mapped[str] = mapped_column(String(150), nullable=False)
    username: Mapped[str] = mapped_column(String(150), nullable=False)
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Theme(Base, UUIDPrimaryKeyMixin):
    """UI theme configuration."""

    __tablename__ = "themes"

    theme_name: Mapped[str] = mapped_column(String(100), nullable=False)
    primary_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    secondary_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    accent_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """Immutable administrative audit log."""

    __tablename__ = "audit_logs"

    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    module: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(150), nullable=False)
    old_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(150), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
