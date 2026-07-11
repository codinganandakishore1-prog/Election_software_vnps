"""Audit log repository."""

from sqlalchemy.orm import Session

from app.models.settings import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Data access for audit log records."""

    model = AuditLog

    def __init__(self, db: Session) -> None:
        super().__init__(db)
