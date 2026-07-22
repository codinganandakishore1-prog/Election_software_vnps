"""Synchronization service tests."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from election_platform.enums.election import ElectionStatus, ElectionType

from app.exceptions.base import ForbiddenError, ValidationError
from app.schemas.sync import VotePayload, VoteUploadRequest
from app.services.sync_service import SyncService


def _make_vote_payload(**overrides) -> VotePayload:
    return VotePayload(
        vote_uuid=overrides.get("vote_uuid", "vote-1"),
        election_id=overrides.get("election_id", "election-1"),
        position_id=overrides.get("position_id", "position-1"),
        candidate_id=overrides.get("candidate_id", "candidate-1"),
        election_type=overrides.get("election_type", "Regular"),
        house_id=overrides.get("house_id"),
        timestamp=overrides.get("timestamp", "2027-07-20T10:30:45+00:00"),
    )


def _make_service(**overrides) -> SyncService:
    vote_repo = overrides.get("vote_repository", MagicMock())
    if "vote_repository" not in overrides:
        vote_repo.exists_by_vote_uuid.return_value = False

    node = MagicMock()
    node.id = "node-1"
    node.active = True
    node.config_version = 5
    node.election_type = ElectionType.REGULAR

    node_repo = overrides.get("node_repository", MagicMock())
    node_repo.get_by_id.return_value = node

    election = MagicMock()
    election.deleted_at = None

    election_repo = overrides.get("election_repository", MagicMock())
    election_repo.get_by_id.return_value = election

    position = MagicMock()
    position.deleted_at = None
    position.election_id = "election-1"

    position_repo = overrides.get("position_repository", MagicMock())
    position_repo.get_by_id.return_value = position

    candidate_repo = overrides.get("candidate_repository", MagicMock())
    if "candidate_repository" not in overrides:
        candidate = MagicMock()
        candidate.deleted_at = None
        candidate.position_id = "position-1"
        candidate.election_id = "election-1"
        candidate_repo.get_by_id.return_value = candidate

    vote_queue_repo = overrides.get("vote_queue_repository", MagicMock())
    if "vote_queue_repository" not in overrides:
        vote_queue_repo.get_by_vote_uuid.return_value = None

    return SyncService(
        vote_repository=vote_repo,
        node_repository=node_repo,
        election_repository=election_repo,
        position_repository=position_repo,
        candidate_repository=candidate_repo,
        vote_queue_repository=vote_queue_repo,
        sync_log_repository=overrides.get("sync_log_repository", MagicMock()),
        audit_log_repository=overrides.get("audit_log_repository", MagicMock()),
    )


def test_upload_votes_accepts_valid_vote() -> None:
    service = _make_service()
    payload = VoteUploadRequest(
        node_id="node-1",
        config_version=5,
        votes=[_make_vote_payload()],
    )

    result = service.upload_votes(payload, "node-1")

    assert result.accepted == ["vote-1"]
    assert result.duplicates == []
    assert result.failed == []
    service.vote_repository.add.assert_called_once()
    service.vote_repository.commit.assert_called_once()


def test_upload_votes_detects_duplicate() -> None:
    vote_repo = MagicMock()
    vote_repo.exists_by_vote_uuid.return_value = True

    service = _make_service(vote_repository=vote_repo)
    payload = VoteUploadRequest(
        node_id="node-1",
        config_version=5,
        votes=[_make_vote_payload()],
    )

    result = service.upload_votes(payload, "node-1")

    assert result.duplicates == ["vote-1"]
    assert result.accepted == []
    vote_repo.add.assert_not_called()


def test_upload_votes_rejects_config_version_mismatch() -> None:
    service = _make_service()
    payload = VoteUploadRequest(
        node_id="node-1",
        config_version=99,
        votes=[_make_vote_payload()],
    )

    with pytest.raises(ValidationError, match="Configuration version mismatch"):
        service.upload_votes(payload, "node-1")


def test_upload_votes_rejects_node_mismatch() -> None:
    service = _make_service()
    payload = VoteUploadRequest(
        node_id="node-1",
        config_version=5,
        votes=[_make_vote_payload()],
    )

    with pytest.raises(ForbiddenError, match="Token does not match node"):
        service.upload_votes(payload, "other-node")


def test_upload_votes_marks_invalid_candidate_as_failed() -> None:
    candidate_repo = MagicMock()
    candidate_repo.get_by_id.return_value = None

    service = _make_service(candidate_repository=candidate_repo)
    payload = VoteUploadRequest(
        node_id="node-1",
        config_version=5,
        votes=[_make_vote_payload()],
    )

    result = service.upload_votes(payload, "node-1")

    assert result.failed == ["vote-1"]
    service.vote_queue_repository.add.assert_called_once()
