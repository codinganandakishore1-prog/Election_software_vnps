"""Desktop repository layer."""

from app.repositories.base import LocalBaseRepository
from app.repositories.local_vote_repository import LocalVoteRepository
from app.repositories.queue_repository import LocalQueueRepository
from app.repositories.settings_repository import LocalSettingsRepository

__all__ = [
    "LocalBaseRepository",
    "LocalQueueRepository",
    "LocalSettingsRepository",
    "LocalVoteRepository",
]
