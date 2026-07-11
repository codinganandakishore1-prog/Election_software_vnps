"""Position management service (placeholder)."""

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.position_repository import PositionRepository
from app.services.base import BaseService


class PositionService(BaseService):
    """Handles position CRUD operations."""

    def __init__(self, position_repository: PositionRepository, audit_log_repository: AuditLogRepository) -> None:
        self.position_repository = position_repository
        self.audit_log_repository = audit_log_repository
