"""Repository layer."""

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.backup_repository import BackupRepository
from app.repositories.base import BaseRepository
from app.repositories.candidate_repository import CandidateImageRepository, CandidateRepository
from app.repositories.election_repository import ElectionRepository
from app.repositories.house_repository import HouseRepository
from app.repositories.node_repository import (
    NodeDownloadRepository,
    NodeHeartbeatRepository,
    NodeRepository,
    NodeSessionRepository,
    PublishedConfigurationRepository,
    SyncLogRepository,
    VoteQueueRepository,
)
from app.repositories.notification_repository import NotificationRepository
from app.repositories.position_repository import PositionRepository
from app.repositories.report_repository import (
    ReportDownloadRepository,
    ReportRepository,
    ReportTemplateRepository,
)
from app.repositories.role_repository import RoleRepository
from app.repositories.session_repository import UserSessionRepository
from app.repositories.settings_repository import (
    MySQLSettingsRepository,
    SettingsRepository,
    ThemeRepository,
)
from app.repositories.user_repository import LoginHistoryRepository, UserRepository
from app.repositories.vote_repository import VoteRepository

__all__ = [
    "AuditLogRepository",
    "BackupRepository",
    "BaseRepository",
    "CandidateImageRepository",
    "CandidateRepository",
    "ElectionRepository",
    "HouseRepository",
    "LoginHistoryRepository",
    "MySQLSettingsRepository",
    "NodeDownloadRepository",
    "NodeHeartbeatRepository",
    "NodeRepository",
    "NodeSessionRepository",
    "NotificationRepository",
    "PositionRepository",
    "PublishedConfigurationRepository",
    "ReportDownloadRepository",
    "ReportRepository",
    "ReportTemplateRepository",
    "RoleRepository",
    "UserSessionRepository",
    "SettingsRepository",
    "SyncLogRepository",
    "ThemeRepository",
    "UserRepository",
    "VoteQueueRepository",
    "VoteRepository",
]
