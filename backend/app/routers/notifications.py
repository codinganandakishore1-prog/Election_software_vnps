"""Notifications router."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter

from app.dependencies.auth import CurrentUser
from app.dependencies.providers import ServiceContainer
from app.schemas.notification import NotificationResponse

router = APIRouter()


@router.get("")
async def list_notifications(
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[list[NotificationResponse]]:
    """List notifications for the authenticated user."""
    notifications = container.notification_service.list_for_user(str(current_user.id))
    return APIResponse.ok(data=notifications)


@router.get("/recent")
async def list_recent_notifications(
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[list[NotificationResponse]]:
    """List recent global and user notifications."""
    _ = current_user
    notifications = container.notification_service.list_recent()
    return APIResponse.ok(data=notifications)


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[NotificationResponse]:
    """Mark a notification as read."""
    notification = container.notification_service.mark_read(notification_id, str(current_user.id))
    return APIResponse.ok(message="Notification marked as read", data=notification)
