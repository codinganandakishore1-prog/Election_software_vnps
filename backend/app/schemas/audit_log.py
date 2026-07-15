"""Audit log API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Single immutable audit log entry."""

    id: str
    user_id: str | None
    user_name: str | None
    module: str
    action: str
    old_value: dict[str, Any] | None
    new_value: dict[str, Any] | None
    ip_address: str | None
    browser: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogPageResponse(BaseModel):
    """Paginated audit log results."""

    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int


class AuditLogFilterParams(BaseModel):
    """Query filters for audit log search."""

    module: str | None = None
    user_id: str | None = None
    action: str | None = None
    search: str | None = Field(default=None, max_length=200)
    from_date: datetime | None = None
    to_date: datetime | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
