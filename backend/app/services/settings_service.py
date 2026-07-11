"""Website settings service (placeholder)."""

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.settings_repository import SettingsRepository
from app.services.base import BaseService


class SettingsService(BaseService):
    """Handles website and database settings."""

    def __init__(self, settings_repository: SettingsRepository, audit_log_repository: AuditLogRepository) -> None:
        self.settings_repository = settings_repository
        self.audit_log_repository = audit_log_repository
