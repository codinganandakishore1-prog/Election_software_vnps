"""Shared enumerations used across backend, website, and desktop."""

from election_platform.enums.election import ElectionStatus, ElectionType
from election_platform.enums.roles import UserRole
from election_platform.enums.sync import QueueStatus, SyncStatus

__all__ = [
    "ElectionStatus",
    "ElectionType",
    "UserRole",
    "QueueStatus",
    "SyncStatus",
]
