"""Desktop ORM models."""

from app.models.desktop_setting import LocalSetting
from app.models.local_vote import LocalVote
from app.models.queue import LocalQueueItem

__all__ = ["LocalQueueItem", "LocalSetting", "LocalVote"]
