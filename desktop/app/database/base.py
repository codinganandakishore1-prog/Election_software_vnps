"""SQLAlchemy declarative base and mixins for desktop local storage."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LocalBase(DeclarativeBase):
    """Base class for desktop ORM models."""


class UUIDPrimaryKeyMixin:
    """UUID primary key mixin (CHAR(36))."""

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
