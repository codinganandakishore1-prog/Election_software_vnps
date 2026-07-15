"""Serialize local votes for synchronization uploads."""

from __future__ import annotations

from app.models.local_vote import LocalVote
from app.services.local_vote_queue_service import VoteRecord


def vote_record_from_local_vote(vote: LocalVote) -> VoteRecord:
    """Convert a persisted local vote row into a VoteRecord."""
    return VoteRecord(
        vote_uuid=vote.vote_uuid,
        election_id=vote.election_id,
        position_id=vote.position_id,
        candidate_id=vote.candidate_id,
        node_id=vote.node_id,
        election_type=vote.election_type,
        house_id=vote.house_id,
    )


def serialize_vote_payload(vote: LocalVote) -> dict:
    """Build the REST payload for a single vote."""
    return {
        "vote_uuid": vote.vote_uuid,
        "election_id": vote.election_id,
        "position_id": vote.position_id,
        "candidate_id": vote.candidate_id,
        "election_type": vote.election_type,
        "house_id": vote.house_id,
        "timestamp": vote.created_at.isoformat(),
    }


def build_upload_request(
    *,
    node_id: str,
    config_version: int,
    votes: list[LocalVote],
) -> dict:
    """Build the batch upload request body from ORM rows."""
    return build_upload_request_from_payloads(
        node_id=node_id,
        config_version=config_version,
        votes=[serialize_vote_payload(vote) for vote in votes],
    )


def build_upload_request_from_payloads(
    *,
    node_id: str,
    config_version: int,
    votes: list[dict],
) -> dict:
    """Build the batch upload request body from serialized vote dicts."""
    return {
        "node_id": node_id,
        "config_version": config_version,
        "votes": votes,
    }
