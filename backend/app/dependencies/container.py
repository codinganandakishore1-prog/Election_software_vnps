"""Service container and dependency injection wiring."""

from functools import lru_cache

from sqlalchemy.orm import Session

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.candidate_repository import CandidateImageRepository, CandidateRepository
from app.repositories.election_repository import ElectionRepository
from app.repositories.house_repository import HouseRepository
from app.repositories.node_repository import (
    NodeHeartbeatRepository,
    NodeRepository,
    NodeSessionRepository,
    PublishedConfigurationRepository,
    SyncLogRepository,
    VoteQueueRepository,
)
from app.repositories.notification_repository import NotificationRepository
from app.repositories.position_repository import PositionRepository
from app.repositories.report_repository import ReportDownloadRepository, ReportRepository
from app.repositories.session_repository import UserSessionRepository
from app.repositories.settings_repository import MySQLSettingsRepository, SettingsRepository, ThemeRepository
from app.repositories.user_repository import LoginHistoryRepository, UserRepository
from app.repositories.vote_repository import VoteRepository
from app.security.jwt import JWTHandler
from app.security.password import PasswordHasher
from app.services.analytics_service import AnalyticsService
from app.services.audit_log_service import AuditLogService
from app.services.auth_service import AuthService
from app.services.candidate_service import CandidateService
from app.services.config_package_service import ConfigPackageService
from app.services.election_service import ElectionService
from app.services.house_service import HouseService
from app.services.image_service import ImageService
from app.services.node_service import NodeService
from app.services.notification_service import NotificationService
from app.services.position_service import PositionService
from app.services.report_service import ReportService
from app.services.settings_service import SettingsService
from app.services.sync_service import SyncService
from app.services.theme_service import ThemeService
from app.services.user_service import UserService


class Container:
    """Application service container."""

    def __init__(self, db: Session) -> None:
        self.db = db

        # Repositories
        self.user_repository = UserRepository(db)
        self.login_history_repository = LoginHistoryRepository(db)
        self.user_session_repository = UserSessionRepository(db)
        self.election_repository = ElectionRepository(db)
        self.candidate_repository = CandidateRepository(db)
        self.candidate_image_repository = CandidateImageRepository(db)
        self.position_repository = PositionRepository(db)
        self.node_repository = NodeRepository(db)
        self.node_heartbeat_repository = NodeHeartbeatRepository(db)
        self.node_session_repository = NodeSessionRepository(db)
        self.vote_repository = VoteRepository(db)
        self.report_repository = ReportRepository(db)
        self.report_download_repository = ReportDownloadRepository(db)
        self.settings_repository = SettingsRepository(db)
        self.mysql_settings_repository = MySQLSettingsRepository(db)
        self.house_repository = HouseRepository(db)
        self.audit_log_repository = AuditLogRepository(db)
        self.published_configuration_repository = PublishedConfigurationRepository(db)
        self.theme_repository = ThemeRepository(db)
        self.vote_queue_repository = VoteQueueRepository(db)
        self.sync_log_repository = SyncLogRepository(db)
        self.notification_repository = NotificationRepository(db)

        # Security
        self.jwt_handler = JWTHandler()
        self.password_hasher = PasswordHasher()

        # Services
        self.auth_service = AuthService(
            self.user_repository,
            self.login_history_repository,
            self.user_session_repository,
            self.node_repository,
            self.node_session_repository,
            self.audit_log_repository,
            jwt_handler=self.jwt_handler,
            password_hasher=self.password_hasher,
        )
        self.user_service = UserService(
            self.user_repository,
            self.audit_log_repository,
            password_hasher=self.password_hasher,
        )
        self.config_package_service = ConfigPackageService(
            self.election_repository,
            self.position_repository,
            self.candidate_repository,
            self.candidate_image_repository,
            self.house_repository,
            self.settings_repository,
            self.theme_repository,
        )
        self.house_service = HouseService(
            self.house_repository,
            self.position_repository,
            self.candidate_repository,
            self.election_repository,
            self.node_repository,
            self.audit_log_repository,
        )
        self.election_service = ElectionService(
            self.election_repository,
            self.position_repository,
            self.candidate_repository,
            self.published_configuration_repository,
            self.audit_log_repository,
            self.config_package_service,
            self.house_service,
        )
        self.candidate_service = CandidateService(
            self.candidate_repository,
            self.position_repository,
            self.election_repository,
            self.house_repository,
            self.audit_log_repository,
        )
        self.position_service = PositionService(
            self.position_repository,
            self.election_repository,
            self.candidate_repository,
            self.audit_log_repository,
        )
        self.image_service = ImageService(
            self.candidate_repository,
            self.candidate_image_repository,
            self.audit_log_repository,
        )
        self.node_service = NodeService(
            self.node_repository,
            self.node_heartbeat_repository,
            self.house_repository,
            self.election_repository,
            self.audit_log_repository,
            password_hasher=self.password_hasher,
        )
        self.sync_service = SyncService(
            self.vote_repository,
            self.node_repository,
            self.election_repository,
            self.position_repository,
            self.candidate_repository,
            self.vote_queue_repository,
            self.sync_log_repository,
            self.audit_log_repository,
        )
        self.report_service = ReportService(
            self.report_repository,
            self.report_download_repository,
            self.audit_log_repository,
            self.election_repository,
            self.position_repository,
            self.candidate_repository,
            self.house_repository,
            self.node_repository,
            self.vote_repository,
            self.settings_repository,
            self.theme_repository,
            self.user_repository,
        )
        self.analytics_service = AnalyticsService(
            self.vote_repository,
            self.election_repository,
            self.node_repository,
            self.node_heartbeat_repository,
            self.vote_queue_repository,
            self.candidate_repository,
            self.position_repository,
            self.house_repository,
            self.settings_repository,
            self.theme_repository,
            self.node_service,
        )
        self.notification_service = NotificationService(self.notification_repository)
        self.audit_log_service = AuditLogService(self.audit_log_repository, self.user_repository)
        self.settings_service = SettingsService(
            self.settings_repository,
            self.mysql_settings_repository,
            self.audit_log_repository,
        )
        self.theme_service = ThemeService(self.theme_repository, self.audit_log_repository)


@lru_cache
def get_container_class() -> type[Container]:
    return Container


def get_container(db: Session) -> Container:
    """Build a request-scoped service container."""
    return get_container_class()(db)
