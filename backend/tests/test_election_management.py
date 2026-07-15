"""Election management service tests."""

from unittest.mock import MagicMock

import pytest
from election_platform.enums.election import ElectionStatus, ElectionType

from app.exceptions.base import ValidationError
from app.schemas.election import ElectionCreate, ElectionUpdate
from app.services.election_service import ElectionService


from datetime import datetime, timezone


def _make_election(**kwargs) -> MagicMock:
    election = MagicMock()
    election.id = kwargs.get("id", "election-1")
    election.election_name = kwargs.get("election_name", "Annual Election")
    election.academic_year = kwargs.get("academic_year", "2026-2027")
    election.description = kwargs.get("description", "Test election")
    election.version = kwargs.get("version", 0)
    election.status = kwargs.get("status", ElectionStatus.DRAFT)
    election.configuration_locked = kwargs.get("configuration_locked", False)
    election.start_time = kwargs.get("start_time")
    election.end_time = kwargs.get("end_time")
    election.logo_path = kwargs.get("logo_path")
    election.created_by = kwargs.get("created_by")
    election.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
    election.updated_at = kwargs.get("updated_at", datetime.now(timezone.utc))
    election.deleted_at = kwargs.get("deleted_at")
    election.active = kwargs.get("active", True)
    return election


def _make_service(**overrides) -> ElectionService:
    election_repo = overrides.get("election_repository", MagicMock())
    position_repo = overrides.get("position_repository", MagicMock())
    candidate_repo = overrides.get("candidate_repository", MagicMock())
    published_repo = overrides.get("published_configuration_repository", MagicMock())
    published_repo.get_latest_for_election.return_value = None
    house_service = overrides.get("house_service", MagicMock())

    config_package_service = overrides.get("config_package_service", MagicMock())
    config_package_service.build_package.return_value = MagicMock(
        package_path="/tmp/pkg.zip",
        checksum="abc123",
        package_size=1024,
    )

    return ElectionService(
        election_repository=election_repo,
        position_repository=position_repo,
        candidate_repository=candidate_repo,
        published_configuration_repository=published_repo,
        audit_log_repository=MagicMock(),
        config_package_service=config_package_service,
        house_service=house_service,
    )


def test_create_election_rejects_duplicate_name() -> None:
    election_repo = MagicMock()
    election_repo.get_by_name.return_value = _make_election()

    service = _make_service(election_repository=election_repo)

    with pytest.raises(ValidationError, match="already exists"):
        service.create_election(ElectionCreate(name="Annual Election"))


def test_delete_election_blocked_when_published() -> None:
    election_repo = MagicMock()
    election_repo.get_by_id.return_value = _make_election(status=ElectionStatus.PUBLISHED)

    service = _make_service(election_repository=election_repo)

    with pytest.raises(ValidationError, match="Cannot delete"):
        service.delete_election("election-1")


def test_publish_increments_version_and_builds_package() -> None:
    election = _make_election(version=2)
    election_repo = MagicMock()
    election_repo.get_by_id.return_value = election

    position = MagicMock()
    position.id = "pos-1"
    position.position_name = "Head Boy"
    position.election_type = ElectionType.REGULAR

    position_repo = MagicMock()
    position_repo.list_for_election.return_value = [position]

    candidate = MagicMock()
    candidate.deleted_at = None
    candidate.candidate_name = "Alice"
    candidate.image_id = "img-1"

    candidate_repo = MagicMock()
    candidate_repo.list_for_position.return_value = [candidate]
    candidate_repo.list_for_election.return_value = [candidate]

    service = _make_service(
        election_repository=election_repo,
        position_repository=position_repo,
        candidate_repository=candidate_repo,
    )

    result = service.publish_election("election-1", user_id="user-1")

    assert result.version == 3
    assert result.checksum == "abc123"
    assert election.status == ElectionStatus.PUBLISHED
    service.config_package_service.build_package.assert_called_once_with(election, 3)


def test_lock_election_sets_configuration_locked() -> None:
    election = _make_election(configuration_locked=False)
    election_repo = MagicMock()
    election_repo.get_by_id.return_value = election

    service = _make_service(election_repository=election_repo)
    result = service.lock_election("election-1")

    assert result.configuration_locked is True
    assert election.configuration_locked is True


def test_duplicate_election_creates_copy_with_unique_name() -> None:
    source = _make_election(election_name="School Election")
    election_repo = MagicMock()
    election_repo.get_by_id.return_value = source
    election_repo.get_by_name.return_value = None

    position = MagicMock()
    position.id = "pos-1"
    position.election_type = MagicMock()
    position.position_name = "Captain"
    position.winner_count = 1
    position.display_order = 1

    position_repo = MagicMock()
    position_repo.list_for_election.return_value = [position]

    candidate = MagicMock()
    candidate.position_id = "pos-1"
    candidate.house_id = None
    candidate.candidate_name = "Bob"
    candidate.display_order = 1
    candidate.image_id = None

    candidate_repo = MagicMock()
    candidate_repo.list_for_election.return_value = [candidate]

    service = _make_service(
        election_repository=election_repo,
        position_repository=position_repo,
        candidate_repository=candidate_repo,
    )

    service.duplicate_election("election-1")

    added_election = election_repo.add.call_args[0][0]
    assert added_election.election_name == "School Election (Copy)"
    assert added_election.status == ElectionStatus.DRAFT
    assert added_election.version == 0
    position_repo.add.assert_called_once()
    candidate_repo.add.assert_called_once()


def test_archive_completed_election() -> None:
    election = _make_election(status=ElectionStatus.COMPLETED)
    election_repo = MagicMock()
    election_repo.get_by_id.return_value = election

    service = _make_service(election_repository=election_repo)
    result = service.archive_election("election-1")

    assert election.status == ElectionStatus.ARCHIVED
    assert election.configuration_locked is True
    assert result.status == ElectionStatus.ARCHIVED


def test_update_election_rejects_live_status() -> None:
    election = _make_election(status=ElectionStatus.LIVE)
    election_repo = MagicMock()
    election_repo.get_by_id.return_value = election

    service = _make_service(election_repository=election_repo)

    from app.exceptions.base import ElectionLockedError

    with pytest.raises(ElectionLockedError):
        service.update_election("election-1", ElectionUpdate(name="New Name"))
