"""User and role ORM models."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Role(Base, UUIDPrimaryKeyMixin):
    """System role."""

    __tablename__ = "roles"

    role_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Administrator and viewer accounts."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("roles.id"), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    role: Mapped[Role] = relationship(back_populates="users")


class LoginHistory(Base, UUIDPrimaryKeyMixin):
    """Login activity history."""

    __tablename__ = "login_history"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    login_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    logout_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(150), nullable=True)
    login_status: Mapped[str] = mapped_column(String(20), nullable=False)
