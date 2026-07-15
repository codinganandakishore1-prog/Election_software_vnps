"""Candidate service unit tests."""

from unittest.mock import MagicMock

import pytest
from election_platform.enums.election import ElectionStatus, ElectionType

from app.exceptions.base import ElectionLockedError, NotFoundError
from app.schemas.candidate import CandidateCreate
from app.services.candidate_service import CandidateService


def _make_service(**overrides) -> CandidateService:
    return CandidateService(
        candidate_repository=overrides.get("candidate_repository", MagicMock()),
        position_repository=overrides.get("position_repository", MagicMock()),
        election_repository=overrides.get("election_repository", MagicMock()),
        house_repository=overrides.get("house_repository", MagicMock()),
        audit_log_repository=overrides.get("audit_log_repository", MagicMock()),
    )


def test_create_candidate_rejects_locked_election() -> None:
    position = MagicMock()
    position.election_type = ElectionType.REGULAR
    position.deleted_at = None
    position_repo = MagicMock()
    position_repo.get_by_id.return_value = position

    election = MagicMock()
    election.status = ElectionStatus.PUBLISHED
    election.configuration_locked = True
    election.deleted_at = None
    election_repo = MagicMock()
    election_repo.get_by_id.return_value = election

    service = _make_service(position_repository=position_repo, election_repository=election_repo)

    with pytest.raises(ElectionLockedError):
        service.create_candidate(
            CandidateCreate(
                election_id="election-1",
                candidate_name="Alice",
                position_id="position-1",
            )
        )


def test_list_candidates_filters_by_election_type() -> None:
    candidate_a = MagicMock()
    candidate_a.house_id = None
    candidate_repo = MagicMock()
    candidate_repo.list_for_election_type.return_value = [candidate_a]

    service = _make_service(candidate_repository=candidate_repo)
    service._to_response = MagicMock(side_effect=lambda candidate: candidate)  # type: ignore[method-assign]

    results = service.list_candidates(election_id="election-1", election_type=ElectionType.REGULAR)
    assert results == [candidate_a]
    candidate_repo.list_for_election_type.assert_called_once_with("election-1", ElectionType.REGULAR)
