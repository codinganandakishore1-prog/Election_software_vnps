"""Service container and dependency injection wiring."""

from functools import lru_cache

from sqlalchemy.orm import Session

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.election_repository import ElectionRepository
from app.repositories.node_repository import NodeRepository
from app.repositories.position_repository import PositionRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.settings_repository import SettingsRepository
from app.repositories.user_repository import UserRepository
from app.repositories.vote_repository import VoteRepository
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.services.candidate_service import CandidateService
from app.services.election_service import ElectionService
from app.services.image_service import ImageService
from app.services.node_service import NodeService
from app.services.position_service import PositionService
from app.services.report_service import ReportService
from app.services.settings_service import SettingsService
from app.services.sync_service import SyncService
from app.services.user_service import UserService


class Container:
    """Application service container."""

    def __init__(self, db: Session) -> None:
        self.db = db

        # Repositories
        self.user_repository = UserRepository(db)
        self.election_repository = ElectionRepository(db)
        self.candidate_repository = CandidateRepository(db)
        self.position_repository = PositionRepository(db)
        self.node_repository = NodeRepository(db)
        self.vote_repository = VoteRepository(db)
        self.report_repository = ReportRepository(db)
        self.settings_repository = SettingsRepository(db)
        self.audit_log_repository = AuditLogRepository(db)

        # Services
        self.auth_service = AuthService(self.user_repository, self.audit_log_repository)
        self.user_service = UserService(self.user_repository, self.audit_log_repository)
        self.election_service = ElectionService(self.election_repository, self.audit_log_repository)
        self.candidate_service = CandidateService(self.candidate_repository, self.audit_log_repository)
        self.position_service = PositionService(self.position_repository, self.audit_log_repository)
        self.image_service = ImageService(self.candidate_repository, self.audit_log_repository)
        self.node_service = NodeService(self.node_repository, self.audit_log_repository)
        self.sync_service = SyncService(self.vote_repository, self.node_repository, self.audit_log_repository)
        self.report_service = ReportService(self.report_repository, self.audit_log_repository)
        self.analytics_service = AnalyticsService(self.vote_repository, self.election_repository)
        self.settings_service = SettingsService(self.settings_repository, self.audit_log_repository)


@lru_cache
def get_container_class() -> type[Container]:
    return Container


def get_container(db: Session) -> Container:
    """Build a request-scoped service container."""
    return get_container_class()(db)
