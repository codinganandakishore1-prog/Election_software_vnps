"""FakeRedis queue manager for in-memory vote synchronization."""

from __future__ import annotations

import fakeredis


class QueueManager:
    """In-memory primary and retry vote queues using FakeRedis.

    FakeRedis stores vote UUIDs only. Vote payloads live in the local database.
    A seen-set prevents duplicate enqueue operations across restarts when
    combined with persistent storage checks.
    """

    QUEUE_KEY = "vote_sync_queue"
    RETRY_KEY = "vote_sync_retry_queue"
    SEEN_KEY = "vote_sync_seen"

    def __init__(self) -> None:
        self.redis = fakeredis.FakeStrictRedis(decode_responses=True)

    def enqueue(self, vote_uuid: str) -> bool:
        """Add a vote UUID to the primary queue. Returns False if already queued."""
        return self._enqueue(vote_uuid, queue_key=self.QUEUE_KEY)

    def enqueue_retry(self, vote_uuid: str) -> bool:
        """Add a vote UUID to the retry queue. Returns False if already queued."""
        return self._enqueue(vote_uuid, queue_key=self.RETRY_KEY)

    def move_to_retry(self, vote_uuid: str) -> None:
        """Move a vote from the primary queue into the retry queue."""
        self._remove_from_queue(self.QUEUE_KEY, vote_uuid)
        self.redis.sadd(self.SEEN_KEY, vote_uuid)
        if not self._contains_in_queue(self.RETRY_KEY, vote_uuid):
            self.redis.rpush(self.RETRY_KEY, vote_uuid)

    def peek(self) -> str | None:
        """Return the next vote UUID without removing it (primary before retry)."""
        batch = self.peek_batch(1)
        return batch[0] if batch else None

    def peek_batch(self, limit: int) -> list[str]:
        """Return up to ``limit`` vote UUIDs without removing them."""
        if limit <= 0:
            return []

        result: list[str] = []
        for queue_key in (self.QUEUE_KEY, self.RETRY_KEY):
            remaining = limit - len(result)
            if remaining <= 0:
                break
            items = self.redis.lrange(queue_key, 0, remaining - 1)
            result.extend(items)
        return result[:limit]

    def dequeue(self) -> str | None:
        """Remove and return the next vote UUID (primary before retry)."""
        vote_uuid, _queue_key = self.dequeue_next()
        return vote_uuid

    def dequeue_next(self) -> tuple[str | None, str | None]:
        """Remove and return the next vote UUID and the queue it came from."""
        for queue_key in (self.QUEUE_KEY, self.RETRY_KEY):
            vote_uuid = self.redis.lpop(queue_key)
            if vote_uuid:
                return vote_uuid, queue_key
        return None, None

    def acknowledge(self, vote_uuid: str) -> None:
        """Remove a vote from all in-memory queues after server acknowledgment."""
        self._remove_from_queue(self.QUEUE_KEY, vote_uuid)
        self._remove_from_queue(self.RETRY_KEY, vote_uuid)
        self.redis.srem(self.SEEN_KEY, vote_uuid)

    def contains(self, vote_uuid: str) -> bool:
        """Return True if the vote UUID is tracked in either queue."""
        return bool(self.redis.sismember(self.SEEN_KEY, vote_uuid))

    def clear(self) -> None:
        """Reset all in-memory queue state."""
        self.redis.delete(self.QUEUE_KEY, self.RETRY_KEY, self.SEEN_KEY)

    def rebuild(self, primary_uuids: list[str], retry_uuids: list[str]) -> int:
        """Rebuild FakeRedis queues from persistent storage after crash recovery."""
        self.clear()
        added = 0
        for vote_uuid in primary_uuids:
            if self.enqueue(vote_uuid):
                added += 1
        for vote_uuid in retry_uuids:
            if self.enqueue_retry(vote_uuid):
                added += 1
        return added

    def size(self) -> int:
        """Total number of votes waiting in primary and retry queues."""
        return int(self.redis.llen(self.QUEUE_KEY) + self.redis.llen(self.RETRY_KEY))

    def primary_size(self) -> int:
        return int(self.redis.llen(self.QUEUE_KEY))

    def retry_size(self) -> int:
        return int(self.redis.llen(self.RETRY_KEY))

    def _enqueue(self, vote_uuid: str, *, queue_key: str) -> bool:
        if self.redis.sismember(self.SEEN_KEY, vote_uuid):
            return False
        self.redis.sadd(self.SEEN_KEY, vote_uuid)
        self.redis.rpush(queue_key, vote_uuid)
        return True

    def _remove_from_queue(self, queue_key: str, vote_uuid: str) -> None:
        self.redis.lrem(queue_key, 0, vote_uuid)

    def _contains_in_queue(self, queue_key: str, vote_uuid: str) -> bool:
        items = self.redis.lrange(queue_key, 0, -1)
        return vote_uuid in items
