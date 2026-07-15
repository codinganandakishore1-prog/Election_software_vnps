"""Node management service tests."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from election_platform.enums.election import ElectionType
from election_platform.enums.sync import SyncStatus

from app.exceptions.base import ForbiddenError, ValidationError
from app.schemas.house import NodeAssignmentUpdate
from app.schemas.node import HeartbeatRequest, NodeCreate
from app.services.node_service import NodeService


def _make_node_service(**overrides) -> NodeService:
    return NodeService(
        node_repository=overrides.get("node_repository", MagicMock()),
        heartbeat_repository=overrides.get("heartbeat_repository", MagicMock()),
        house_repository=overrides.get("house_repository", MagicMock()),
        election_repository=overrides.get("election_repository", MagicMock()),
        audit_log_repository=MagicMock(),
        password_hasher=overrides.get("password_hasher", MagicMock()),
    )


def test_create_node_generates_uuid_and_secret() -> None:
    node_repo = MagicMock()
    node_repo.get_by_name.return_value = None
    election_repo = MagicMock()
    election_repo.list_by_status.return_value = []
    password_hasher = MagicMock()
    password_hasher.hash_password.return_value = "$2b$hashed"

    service = _make_node_service(
        node_repository=node_repo,
        election_repository=election_repo,
        password_hasher=password_hasher,
    )

    result = service.create_node(
        NodeCreate(node_name="Regular-01", election_type="Regular"),
        user_id="admin-1",
    )

    assert result.id
    assert result.node_name == "Regular-01"
    assert result.election_type == "Regular"
    assert result.node_secret
    password_hasher.hash_password.assert_called_once_with(result.node_secret)
    node_repo.add.assert_called_once()
    node_repo.commit.assert_called_once()


def test_create_node_requires_house_for_house_type() -> None:
    node_repo = MagicMock()
    node_repo.get_by_name.return_value = None
    election_repo = MagicMock()
    election_repo.list_by_status.return_value = []

    service = _make_node_service(node_repository=node_repo, election_repository=election_repo)

    with pytest.raises(ValidationError, match="House assignment is required"):
        service.create_node(NodeCreate(node_name="House-01", election_type="House"))


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

    service = _make_node_service(
        node_repository=node_repo,
        house_repository=house_repo,
        election_repository=election_repo,
    )

    with pytest.raises(ValidationError, match="must not have a house assignment"):
        service.update_node_assignment(
            "node-1",
            NodeAssignmentUpdate(election_type="Regular", house_id="house-1"),
        )


def test_update_node_assignment_can_disable_node() -> None:
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

    service = _make_node_service(node_repository=node_repo, election_repository=election_repo)

    result = service.update_node_assignment("node-1", NodeAssignmentUpdate(active=False))

    assert node.active is False
    assert result.active is False
    node_repo.commit.assert_called_once()


def test_record_heartbeat_persists_metadata() -> None:
    node_repo = MagicMock()
    node = MagicMock()
    node.id = "node-1"
    node.node_name = "Regular-01"
    node.active = True
    node_repo.get_by_id.return_value = node

    heartbeat_repo = MagicMock()
    heartbeat_repo.get_latest_for_node.return_value = None

    service = _make_node_service(node_repository=node_repo, heartbeat_repository=heartbeat_repo)

    last_vote = datetime(2027, 7, 20, 10, 30, 12, tzinfo=timezone.utc)
    result, previous_status, new_status = service.record_heartbeat(
        HeartbeatRequest(
            node_id="node-1",
            app_version="2.0.0",
            config_version=5,
            queue_size=2,
            last_vote_time=last_vote,
            sync_status=SyncStatus.PENDING,
        ),
        ip_address="192.168.1.10",
    )

    assert result.node_name == "Regular-01"
    assert result.status == "Healthy"
    assert new_status == "Online"
    assert node.app_version == "2.0.0"
    assert node.config_version == 5
    heartbeat_repo.add.assert_called_once()
    heartbeat = heartbeat_repo.add.call_args.args[0]
    assert heartbeat.queue_size == 2
    assert heartbeat.last_vote_time == last_vote
    assert heartbeat.sync_status == SyncStatus.PENDING
    assert heartbeat.ip_address == "192.168.1.10"
    node_repo.commit.assert_called_once()


def test_record_heartbeat_rejects_disabled_node() -> None:
    node_repo = MagicMock()
    node = MagicMock()
    node.id = "node-1"
    node.active = False
    node_repo.get_by_id.return_value = node

    service = _make_node_service(node_repository=node_repo)

    with pytest.raises(ForbiddenError, match="disabled"):
        service.record_heartbeat(
            HeartbeatRequest(node_id="node-1", app_version="1.0.0", config_version=0),
        )


def test_get_node_health_reports_online_status() -> None:
    node_repo = MagicMock()
    node = MagicMock()
    node.id = "node-1"
    node.node_name = "Regular-01"
    node.active = True
    node.app_version = "2.0.0"
    node.config_version = 3
    node_repo.get_by_id.return_value = node

    heartbeat_repo = MagicMock()
    heartbeat = MagicMock()
    heartbeat.heartbeat_time = datetime.now(timezone.utc) - timedelta(seconds=5)
    heartbeat.queue_size = 1
    heartbeat.sync_status = SyncStatus.HEALTHY
    heartbeat.last_vote_time = None
    heartbeat.app_version = "2.0.0"
    heartbeat.config_version = 3
    heartbeat_repo.get_latest_for_node.return_value = heartbeat

    service = _make_node_service(node_repository=node_repo, heartbeat_repository=heartbeat_repo)

    health = service.get_node_health("node-1")

    assert health.status == "Online"
    assert health.queue_size == 1
    assert health.config_version == 3
