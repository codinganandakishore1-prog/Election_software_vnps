"""Notification ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING

from election_platform.enums.admin import NotificationType
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, UUIDPrimaryKeyMixin, utc_now
from app.database.enums import enum_column

if TYPE_CHECKING:
    from app.models.user import User


class Notification(Base, UUIDPrimaryKeyMixin, SoftDeleteMixin):
    """System notification."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_notification_type", "notification_type"),
        Index("ix_notifications_created_at", "created_at"),
        Index("ix_notifications_type_read_status", "notification_type", "read_status"),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[NotificationType] = mapped_column(
        enum_column(NotificationType, name="notification_type"),
        nullable=False,
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    read_status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User | None"] = relationship(back_populates="notifications")
