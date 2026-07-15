"""Desktop local settings ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import LocalBase, UUIDPrimaryKeyMixin, utc_now


class LocalSetting(LocalBase, UUIDPrimaryKeyMixin):
    """Key-value local configuration persisted on the voting node."""

    __tablename__ = "settings"
    __table_args__ = (Index("ix_settings_setting_key", "setting_key", unique=True),)

    setting_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    setting_value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
