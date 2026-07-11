"""User management service (placeholder)."""

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


class UserService(BaseService):
    """Handles user CRUD and password operations."""

    def __init__(self, user_repository: UserRepository, audit_log_repository: AuditLogRepository) -> None:
        self.user_repository = user_repository
        self.audit_log_repository = audit_log_repository
