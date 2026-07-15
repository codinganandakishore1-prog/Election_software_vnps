"""Notification API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    """Notification returned to clients."""

    id: str
    title: str
    message: str
    notification_type: str
    read_status: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationCreate(BaseModel):
    """Create a system notification."""

    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    notification_type: str
    user_id: str | None = None
