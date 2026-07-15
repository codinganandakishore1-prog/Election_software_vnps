"""Settings ORM models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.user import User


class SystemSettings(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Website-wide settings (single active record expected)."""

    __tablename__ = "system_settings"
    __table_args__ = (Index("ix_system_settings_maintenance_mode", "maintenance_mode"),)

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
    updated_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updater: Mapped["User | None"] = relationship(back_populates="mysql_settings_updates")


class Theme(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """UI theme and branding configuration."""

    __tablename__ = "themes"

    theme_name: Mapped[str] = mapped_column(String(100), nullable=False)
    school_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    school_logo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    election_logo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    background_light_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    background_dark_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    background_welcome_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    font_heading: Mapped[str | None] = mapped_column(String(100), nullable=True)
    font_body: Mapped[str | None] = mapped_column(String(100), nullable=True)
    font_accent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    secondary_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    accent_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    warning_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    danger_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    background_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    surface_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    text_primary_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    text_secondary_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    icon_app_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    icon_favicon_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
