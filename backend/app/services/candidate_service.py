"""Candidate management service (placeholder)."""

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.candidate_repository import CandidateRepository
from app.services.base import BaseService


class CandidateService(BaseService):
    """Handles candidate CRUD operations."""

    def __init__(self, candidate_repository: CandidateRepository, audit_log_repository: AuditLogRepository) -> None:
        self.candidate_repository = candidate_repository
        self.audit_log_repository = audit_log_repository
