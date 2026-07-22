"""Synchronization-related enumerations."""

from enum import Enum


class SyncStatus(str, Enum):
    """Node synchronization health statuses."""

    HEALTHY = "Healthy"
    SYNCING = "Syncing"
    PENDING = "Pending"
    OFFLINE = "Offline"


class QueueStatus(str, Enum):
    """Vote queue processing statuses."""

    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"
