"""Structured synchronization event logging."""

from __future__ import annotations

from election_platform.logging.setup import get_logger

logger = get_logger("desktop.sync")


class SyncLogger:
    """Log synchronization lifecycle events for diagnostics and audit."""

    def vote_queued(self, vote_uuid: str) -> None:
        logger.info("Queue added: vote %s", vote_uuid)

    def upload_started(self, vote_uuids: list[str]) -> None:
        logger.info("Upload started: %s vote(s)", len(vote_uuids))

    def upload_success(self, accepted: int, duplicates: int) -> None:
        logger.info("Upload success: %s accepted, %s duplicate(s)", accepted, duplicates)

    def upload_failed(self, message: str, *, vote_uuids: list[str] | None = None) -> None:
        if vote_uuids:
            logger.warning("Upload failed for %s vote(s): %s", len(vote_uuids), message)
        else:
            logger.warning("Upload failed: %s", message)

    def ack_received(self, vote_uuid: str) -> None:
        logger.info("ACK received: vote %s", vote_uuid)

    def queue_removed(self, vote_uuid: str) -> None:
        logger.info("Queue removed: vote %s", vote_uuid)

    def retry_scheduled(self, vote_uuid: str, attempt: int, backoff_seconds: int) -> None:
        logger.warning(
            "Retry scheduled: vote %s attempt %s in %ss",
            vote_uuid,
            attempt,
            backoff_seconds,
        )

    def offline(self) -> None:
        logger.info("Offline mode: votes will queue until connectivity returns")

    def duplicate_ignored(self, vote_uuid: str) -> None:
        logger.info("Duplicate ignored: vote %s", vote_uuid)
