"""Report generation service (placeholder)."""

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.report_repository import ReportRepository
from app.services.base import BaseService


class ReportService(BaseService):
    """Handles report generation and export."""

    def __init__(self, report_repository: ReportRepository, audit_log_repository: AuditLogRepository) -> None:
        self.report_repository = report_repository
        self.audit_log_repository = audit_log_repository
