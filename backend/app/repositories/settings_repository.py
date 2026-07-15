"""Settings repositories."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.settings import MySQLSettings, SystemSettings, Theme
from app.repositories.base import BaseRepository


class SettingsRepository(BaseRepository[SystemSettings]):
    """Data access for system settings."""

    model = SystemSettings

    def get_active(self) -> SystemSettings | None:
        stmt = select(SystemSettings).order_by(SystemSettings.updated_at.desc()).limit(1)
        return self.db.scalar(stmt)


class MySQLSettingsRepository(BaseRepository[MySQLSettings]):
    """Data access for MySQL connection settings."""

    model = MySQLSettings

    def get_latest(self) -> MySQLSettings | None:
        stmt = select(MySQLSettings).order_by(MySQLSettings.updated_at.desc()).limit(1)
        return self.db.scalar(stmt)


class ThemeRepository(BaseRepository[Theme]):
    """Data access for UI theme records."""

    model = Theme

    def get_active(self) -> Theme | None:
        stmt = (
            select(Theme)
            .where(Theme.active.is_(True), Theme.deleted_at.is_(None))
            .limit(1)
        )
        return self.db.scalar(stmt)

    def list_active(self, *, limit: int | None = None, offset: int = 0) -> list[Theme]:
        return self.list_by_field("active", True, limit=limit, offset=offset)

    def list_all_ordered(self) -> list[Theme]:
        stmt = (
            select(Theme)
            .where(Theme.deleted_at.is_(None))
            .order_by(Theme.active.desc(), Theme.theme_name.asc())
        )
        return list(self.db.scalars(stmt).all())
