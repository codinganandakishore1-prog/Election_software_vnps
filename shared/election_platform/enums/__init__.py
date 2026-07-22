"""Shared enumerations used across backend, website, and desktop."""

from election_platform.enums.admin import (
    BackupStatus,
    BackupType,
    InstallStatus,
    LocalVoteSyncStatus,
    LoginStatus,
    NotificationType,
    ReportType,
    SessionStatus,
    SyncLogStatus,
)
from election_platform.enums.election import CandidateStatus, ElectionStatus, ElectionType, PositionStatus
from election_platform.enums.roles import UserRole
from election_platform.enums.sync import QueueStatus, SyncStatus

__all__ = [
    "BackupStatus",
    "BackupType",
    "CandidateStatus",
    "ElectionStatus",
    "ElectionType",
    "InstallStatus",
    "LocalVoteSyncStatus",
    "LoginStatus",
    "NotificationType",
    "PositionStatus",
    "QueueStatus",
    "ReportType",
    "SessionStatus",
    "SyncLogStatus",
    "SyncStatus",
    "UserRole",
]
