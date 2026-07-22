"""User session ORM model for JWT refresh tokens and session tracking."""

from datetime import datetime
from typing import TYPE_CHECKING

from election_platform.enums.admin import SessionStatus
from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDPrimaryKeyMixin, utc_now
from app.database.enums import enum_column

if TYPE_CHECKING:
    from app.models.user import User


class UserSession(Base, UUIDPrimaryKeyMixin):
    """Tracks authenticated website user sessions and refresh tokens."""

    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("ix_user_sessions_user_id", "user_id"),
        Index("ix_user_sessions_refresh_token_hash", "refresh_token_hash"),
        Index("ix_user_sessions_session_status", "session_status"),
        Index("ix_user_sessions_expires_at", "expires_at"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    access_token_jti: Mapped[str | None] = mapped_column(String(36), nullable=True)
    login_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    logout_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    session_status: Mapped[SessionStatus] = mapped_column(
        enum_column(SessionStatus, name="user_session_status"),
        nullable=False,
        default=SessionStatus.ACTIVE,
    )
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(150), nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")
