"""FakeRedis queue manager (placeholder)."""

import fakeredis


class QueueManager:
    """In-memory vote queue using FakeRedis."""

    def __init__(self) -> None:
        self.redis = fakeredis.FakeStrictRedis(decode_responses=True)
        self.queue_key = "vote_sync_queue"

    def enqueue(self, vote_uuid: str) -> None:
        self.redis.rpush(self.queue_key, vote_uuid)

    def dequeue(self) -> str | None:
        return self.redis.lpop(self.queue_key)

    def size(self) -> int:
        return self.redis.llen(self.queue_key)
