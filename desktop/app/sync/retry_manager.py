"""Retry scheduling for failed vote synchronization."""

from __future__ import annotations

# SRS retry schedule: 5s → 10s → 20s → 40s → 60s → 60s forever
RETRY_BACKOFF_SECONDS = (5, 10, 20, 40, 60)


class RetryManager:
    """Compute retry delays and track retry attempts."""

    @staticmethod
    def backoff_seconds(retry_count: int) -> int:
        """Return wait time before the next upload attempt."""
        if retry_count < 0:
            return RETRY_BACKOFF_SECONDS[0]
        if retry_count < len(RETRY_BACKOFF_SECONDS):
            return RETRY_BACKOFF_SECONDS[retry_count]
        return RETRY_BACKOFF_SECONDS[-1]

    @staticmethod
    def should_retry(_retry_count: int) -> bool:
        """Votes are never discarded; always retry until acknowledged."""
        return True
