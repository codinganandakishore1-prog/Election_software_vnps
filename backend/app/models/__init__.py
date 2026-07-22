"""SQLAlchemy ORM models — import all models for Alembic metadata discovery."""

from app.models.audit_log import AuditLog
from app.models.backup import Backup
from app.models.candidate import Candidate, CandidateImage
from app.models.election import Election
from app.models.house import House
from app.models.node import NodeDownload, NodeHeartbeat, NodeSession, VotingNode
from app.models.notification import Notification
from app.models.position import Position
from app.models.report import Report, ReportDownload, ReportTemplate
from app.models.settings import MySQLSettings, SystemSettings, Theme
from app.models.sync import PublishedConfiguration, SyncLog, Vote, VoteQueue
from app.models.session import UserSession
from app.models.user import LoginHistory, Role, User

__all__ = [
    "AuditLog",
    "Backup",
    "Candidate",
    "CandidateImage",
    "Election",
    "House",
    "LoginHistory",
    "MySQLSettings",
    "NodeDownload",
    "NodeHeartbeat",
    "NodeSession",
    "Notification",
    "Position",
    "PublishedConfiguration",
    "Report",
    "ReportDownload",
    "ReportTemplate",
    "Role",
    "SyncLog",
    "SystemSettings",
    "Theme",
    "User",
    "UserSession",
    "Vote",
    "VoteQueue",
    "VotingNode",
]
