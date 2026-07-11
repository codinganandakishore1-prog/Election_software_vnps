"""Node management service (placeholder)."""

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.node_repository import NodeRepository
from app.services.base import BaseService


class NodeService(BaseService):
    """Handles node registration, heartbeat, and monitoring."""

    def __init__(self, node_repository: NodeRepository, audit_log_repository: AuditLogRepository) -> None:
        self.node_repository = node_repository
        self.audit_log_repository = audit_log_repository
