"""Vote recording service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from election_platform.logging.setup import get_logger

from app.data.election_store import ElectionStore
from app.exceptions import DuplicateVoteError
from app.services.local_vote_queue_service import LocalVoteQueueService, VoteRecord

logger = get_logger("desktop.vote")


class VoteService:
    """Record votes locally and enqueue for synchronization."""

    def __init__(
        self,
        store: ElectionStore,
        queue_service: LocalVoteQueueService,
    ) -> None:
        self.store = store
        self.queue_service = queue_service

    def record_vote(self, candidate_data: dict) -> dict:
        vote_uuid = str(uuid.uuid4())
        timestamp_formatted = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        position_id = self.store.resolve_position_id(candidate_data)
        election_type = self.store.resolve_election_type(candidate_data)
        house_id = candidate_data.get("house_id") or None

        vote_record = VoteRecord(
            vote_uuid=vote_uuid,
            election_id=self.store.data.get("election_id", ""),
            position_id=position_id,
            candidate_id=candidate_data.get("id", ""),
            node_id=self.store.data.get("node_id") or None,
            election_type=election_type,
            house_id=house_id,
        )

        try:
            self.queue_service.record_and_enqueue(vote_record)
        except DuplicateVoteError as exc:
            logger.error("Duplicate vote rejected: %s", exc)
            raise

        vote_payload = {
            "vote_uuid": vote_uuid,
            "election_id": vote_record.election_id,
            "candidate_id": vote_record.candidate_id,
            "candidate_name": candidate_data.get("name", ""),
            "position": candidate_data.get("position", ""),
            "position_id": position_id,
            "candidate_class": candidate_data.get("candidate_class", ""),
            "candidate_section": candidate_data.get("candidate_section", ""),
            "election_type": election_type,
            "house_id": house_id,
            "timestamp": timestamp_formatted,
        }
        return vote_payload
