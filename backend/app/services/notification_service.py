"""Notification service."""

from __future__ import annotations

from election_platform.enums.admin import NotificationType

from app.database.seeds import new_uuid
from app.exceptions.base import ValidationError
from app.models.notification import Notification
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.services.base import BaseService


class NotificationService(BaseService):
    """Create and deliver system notifications."""

    def __init__(self, notification_repository: NotificationRepository) -> None:
        self.notification_repository = notification_repository

    def list_for_user(self, user_id: str, *, unread_only: bool = False) -> list[NotificationResponse]:
        rows = self.notification_repository.list_for_user(user_id, unread_only=unread_only)
        return [self._to_response(row) for row in rows]

    def list_recent(self, *, limit: int = 20) -> list[NotificationResponse]:
        rows = self.notification_repository.list_unread()[:limit]
        if len(rows) < limit:
            global_rows = self.notification_repository.list_global()
            seen = {row.id for row in rows}
            for row in global_rows:
                if row.id not in seen:
                    rows.append(row)
                if len(rows) >= limit:
                    break
        return [self._to_response(row) for row in rows[:limit]]

    def mark_read(self, notification_id: str, user_id: str) -> NotificationResponse:
        notification = self.notification_repository.get_by_id(notification_id)
        if notification is None:
            raise ValidationError("Notification not found")
        if notification.user_id and notification.user_id != user_id:
            raise ValidationError("Notification not found")
        notification.read_status = True
        self.notification_repository.commit()
        return self._to_response(notification)

    async def create_and_broadcast(
        self,
        *,
        title: str,
        message: str,
        notification_type: str,
        user_id: str | None = None,
    ) -> NotificationResponse:
        payload = NotificationCreate(
            title=title,
            message=message,
            notification_type=notification_type,
            user_id=user_id,
        )
        notification = self.create(payload)
        from app.websocket.broadcaster import broadcast_notification

        await broadcast_notification(notification)
        return notification

    def create(self, payload: NotificationCreate) -> NotificationResponse:
        try:
            note_type = NotificationType(payload.notification_type)
        except ValueError as exc:
            raise ValidationError("Invalid notification type") from exc

        notification = Notification(
            id=new_uuid(),
            title=payload.title.strip(),
            message=payload.message.strip(),
            notification_type=note_type,
            user_id=payload.user_id,
        )
        self.notification_repository.add(notification)
        self.notification_repository.commit()
        return self._to_response(notification)

    @staticmethod
    def _to_response(notification: Notification) -> NotificationResponse:
        return NotificationResponse(
            id=notification.id,
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type.value,
            read_status=notification.read_status,
            created_at=notification.created_at,
        )
