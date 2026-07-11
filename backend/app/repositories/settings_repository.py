"""Settings repository."""

from sqlalchemy.orm import Session

from app.models.settings import SystemSettings
from app.repositories.base import BaseRepository


class SettingsRepository(BaseRepository[SystemSettings]):
    """Data access for system settings records."""

    model = SystemSettings

    def __init__(self, db: Session) -> None:
        super().__init__(db)
