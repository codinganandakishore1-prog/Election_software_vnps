"""House management service tests."""

from unittest.mock import MagicMock

import pytest
from election_platform.enums.election import ElectionType

from app.schemas.house import HouseConfigurationRequest, NodeAssignmentUpdate
from app.services.candidate_service import CandidateService
from app.services.house_service import HouseService
from app.services.node_service import NodeService
from app.exceptions.base import ValidationError


def _make_house_service(**overrides) -> HouseService:
    return HouseService(
        house_repository=overrides.get("house_repository", MagicMock()),
        position_repository=overrides.get("position_repository", MagicMock()),
        candidate_repository=overrides.get("candidate_repository", MagicMock()),
        election_repository=overrides.get("election_repository", MagicMock()),
        node_repository=overrides.get("node_repository", MagicMock()),
        audit_log_repository=MagicMock(),
    )


def test_list_house_names_returns_seed_order() -> None:
    house_repo = MagicMock()
    house_repo.list_all_ordered.return_value = [
        MagicMock(house_name="Pallava"),
        MagicMock(house_name="Pandya"),
        MagicMock(house_name="Chera"),
        MagicMock(house_name="Chola"),
    ]
    service = _make_house_service(house_repository=house_repo)

    assert service.list_house_names() == ["Pallava", "Pandya", "Chera", "Chola"]


def test_configure_positions_rejects_duplicate_names() -> None:
    election_repo = MagicMock()
    election = MagicMock()
    election.deleted_at = None
    election.status = "Draft"
    election_repo.get_by_id.return_value = election

    service = _make_house_service(election_repository=election_repo)

    with pytest.raises(ValidationError, match="Duplicate house position names"):
        service.configure_positions(
            HouseConfigurationRequest(
                election_id="election-1",
                positions=["House Captain", "house captain"],
            )
        )


def test_validate_reports_missing_house_positions() -> None:
    election_repo = MagicMock()
    election = MagicMock()
    election.deleted_at = None
    election_repo.get_by_id.return_value = election

    house_repo = MagicMock()
    house_repo.list_all_ordered.return_value = [MagicMock(id=f"h{i}", house_name=name) for i, name in enumerate(
        ["Pallava", "Pandya", "Chera", "Chola"],
        start=1,
    )]

    position_repo = MagicMock()
    position_repo.list_by_election_type.return_value = []

    node_repo = MagicMock()
    node_repo.list_all_ordered.return_value = []

    service = _make_house_service(
        election_repository=election_repo,
        house_repository=house_repo,
        position_repository=position_repo,
        node_repository=node_repo,
    )

    result = service.validate("election-1")
    assert result.valid is False
    assert any("at least one leadership position" in error for error in result.errors)


def test_node_service_rejects_regular_node_with_house() -> None:
    node_repo = MagicMock()
    node = MagicMock()
    node.id = "node-1"
    node.node_name = "Regular-01"
    node.election_type = ElectionType.REGULAR
    node.house_id = None
    node.house = None
    node.config_version = 1
    node.active = True
    node_repo.get_by_id.return_value = node

    election_repo = MagicMock()
    election_repo.list_by_status.return_value = []

    house_repo = MagicMock()
    house = MagicMock()
    house.active = True
    house_repo.get_by_id.return_value = house

    service = NodeService(
        node_repository=node_repo,
        heartbeat_repository=MagicMock(),
        house_repository=house_repo,
        election_repository=election_repo,
        audit_log_repository=MagicMock(),
    )

    with pytest.raises(ValidationError, match="must not have a house assignment"):
        service.update_node_assignment(
            "node-1",
            NodeAssignmentUpdate(election_type="Regular", house_id="house-1"),
        )


def test_candidate_service_requires_house_for_house_election() -> None:
    position_repo = MagicMock()
    position = MagicMock()
    position.id = "position-1"
    position.election_type = ElectionType.HOUSE
    position.election_id = "election-1"
    position.deleted_at = None
    position_repo.get_by_id.return_value = position

    election_repo = MagicMock()
    election = MagicMock()
    election.deleted_at = None
    election.status = "Draft"
    election_repo.get_by_id.return_value = election

    service = CandidateService(
        candidate_repository=MagicMock(),
        position_repository=position_repo,
        election_repository=election_repo,
        house_repository=MagicMock(),
        audit_log_repository=MagicMock(),
    )

    payload = MagicMock(
        election_id="election-1",
        position_id="position-1",
        candidate_name="Alex",
        house_id=None,
        display_order=1,
    )

    with pytest.raises(ValidationError, match="House is required"):
        service.create_candidate(payload)


def test_candidate_service_rejects_house_on_regular_candidate() -> None:
    position_repo = MagicMock()
    position = MagicMock()
    position.id = "position-1"
    position.election_type = ElectionType.REGULAR
    position.election_id = "election-1"
    position.deleted_at = None
    position_repo.get_by_id.return_value = position

    election_repo = MagicMock()
    election = MagicMock()
    election.deleted_at = None
    election.status = "Draft"
    election_repo.get_by_id.return_value = election

    service = CandidateService(
        candidate_repository=MagicMock(),
        position_repository=position_repo,
        election_repository=election_repo,
        house_repository=MagicMock(),
        audit_log_repository=MagicMock(),
    )

    payload = MagicMock(
        election_id="election-1",
        position_id="position-1",
        candidate_name="Alex",
        house_id="house-1",
        display_order=1,
    )

    with pytest.raises(ValidationError, match="must not have a house assignment"):
        service.create_candidate(payload)
