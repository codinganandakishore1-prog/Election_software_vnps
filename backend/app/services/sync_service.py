"""Vote synchronization service (placeholder)."""

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.node_repository import NodeRepository
from app.repositories.vote_repository import VoteRepository
from app.services.base import BaseService


class SyncService(BaseService):
    """Handles vote upload, validation, and queue processing."""

    def __init__(
        self,
        vote_repository: VoteRepository,
        node_repository: NodeRepository,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        self.vote_repository = vote_repository
        self.node_repository = node_repository
        self.audit_log_repository = audit_log_repository
