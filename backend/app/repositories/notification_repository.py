"""Notification repository."""

from election_platform.enums.admin import NotificationType
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Data access for system notifications."""

    model = Notification

    def list_for_user(self, user_id: str, *, unread_only: bool = False) -> list[Notification]:
        stmt = select(Notification).where(
            ((Notification.user_id == user_id) | (Notification.user_id.is_(None))),
            Notification.active.is_(True),
            Notification.deleted_at.is_(None),
        )
        if unread_only:
            stmt = stmt.where(Notification.read_status.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def list_global(self) -> list[Notification]:
        stmt = select(Notification).where(
            Notification.user_id.is_(None),
            Notification.active.is_(True),
            Notification.deleted_at.is_(None),
        )
        return list(self.db.scalars(stmt).all())

    def list_by_type(self, notification_type: NotificationType) -> list[Notification]:
        return self.list_by_field("notification_type", notification_type)

    def list_unread(self) -> list[Notification]:
        stmt = select(Notification).where(
            Notification.read_status.is_(False),
            Notification.active.is_(True),
            Notification.deleted_at.is_(None),
        )
        return list(self.db.scalars(stmt).all())
