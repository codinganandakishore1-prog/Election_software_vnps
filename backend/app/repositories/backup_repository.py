"""Backup repository."""

from election_platform.enums.admin import BackupStatus, BackupType
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.backup import Backup
from app.repositories.base import BaseRepository


class BackupRepository(BaseRepository[Backup]):
    """Data access for backup records."""

    model = Backup

    def list_by_type(self, backup_type: BackupType) -> list[Backup]:
        stmt = (
            select(Backup)
            .where(Backup.backup_type == backup_type)
            .order_by(Backup.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_status(self, status: BackupStatus) -> list[Backup]:
        return self.list_by_field("status", status)
