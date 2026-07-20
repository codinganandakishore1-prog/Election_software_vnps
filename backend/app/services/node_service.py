"""Node management service."""

from __future__ import annotations

import secrets
from datetime import timedelta, timezone

from election_platform.enums.election import ElectionStatus, ElectionType
from election_platform.enums.sync import SyncStatus

from app.config.settings import settings
from app.database.base import utc_now
from app.database.seeds import new_uuid
from app.exceptions.base import ElectionLockedError, ForbiddenError, NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.node import NodeHeartbeat, VotingNode
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.election_repository import ElectionRepository
from app.repositories.house_repository import HouseRepository
from app.repositories.node_repository import NodeHeartbeatRepository, NodeRepository
from app.schemas.house import NodeAssignmentResponse, NodeAssignmentUpdate
from app.schemas.node import (
    HeartbeatRequest,
    HeartbeatResponse,
    NodeCreate,
    NodeHealthResponse,
    NodeRegistrationResponse,
    NodeResponse,
)
from app.security.password import PasswordHasher
from app.services.base import BaseService


class NodeService(BaseService):
    """Handles node registration, house assignment, and heartbeat."""

    def __init__(
        self,
        node_repository: NodeRepository,
        heartbeat_repository: NodeHeartbeatRepository,
        house_repository: HouseRepository,
        election_repository: ElectionRepository,
        audit_log_repository: AuditLogRepository,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        self.node_repository = node_repository
        self.heartbeat_repository = heartbeat_repository
        self.house_repository = house_repository
        self.election_repository = election_repository
        self.audit_log_repository = audit_log_repository
        self.password_hasher = password_hasher or PasswordHasher()

    def list_nodes(
        self,
        *,
        election_type: ElectionType | None = None,
        house_id: str | None = None,
        active_only: bool = False,
    ) -> list[NodeResponse]:
        nodes = (
            self.node_repository.list_by_election_type(election_type)
            if election_type is not None
            else self.node_repository.list_all_ordered()
        )
        if house_id is not None:
            nodes = [node for node in nodes if node.house_id == house_id]
        if active_only:
            nodes = [node for node in nodes if node.active]
        return [self._to_response(node) for node in nodes]

    def get_node(self, node_id: str) -> NodeResponse:
        node = self._get_node_or_raise(node_id)
        return self._to_response(node)

    def create_node(self, payload: NodeCreate, *, user_id: str | None = None) -> NodeRegistrationResponse:
        self._ensure_nodes_editable()

        node_name = payload.node_name.strip()
        if not node_name:
            raise ValidationError("Node name is required")

        if self.node_repository.get_by_name(node_name) is not None:
            raise ValidationError("A node with this name already exists")

        try:
            election_type = ElectionType(payload.election_type)
        except ValueError as exc:
            raise ValidationError("Invalid election type") from exc

        house_id = payload.house_id if election_type == ElectionType.HOUSE else None
        self._validate_house_assignment(election_type, house_id)

        plain_secret = secrets.token_urlsafe(32)
        node = VotingNode(
            id=new_uuid(),
            node_name=node_name,
            node_secret=self.password_hasher.hash_password(plain_secret),
            election_type=election_type,
            house_id=house_id,
            config_version=0,
            active=payload.active,
        )
        self.node_repository.add(node)
        self.node_repository.flush()

        self._audit(
            user_id,
            "Node Registered",
            {
                "node_id": node.id,
                "node_name": node.node_name,
                "election_type": node.election_type.value,
                "house_id": node.house_id,
            },
        )
        self.node_repository.commit()

        return NodeRegistrationResponse(
            id=node.id,
            node_name=node.node_name,
            election_type=node.election_type.value,
            house_id=node.house_id,
            house_name=node.house.house_name if node.house else None,
            active=node.active,
            config_version=node.config_version,
            node_secret=plain_secret,
        )

    def update_node_assignment(
        self,
        node_id: str,
        payload: NodeAssignmentUpdate,
        *,
        user_id: str | None = None,
    ) -> NodeAssignmentResponse:
        node = self._get_node_or_raise(node_id)
        self._ensure_nodes_editable()

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise ValidationError("No fields provided to update")

        election_type = ElectionType(updates["election_type"]) if "election_type" in updates else node.election_type
        house_id = updates.get("house_id", node.house_id)

        if "node_name" in updates:
            existing = self.node_repository.get_by_name(updates["node_name"])
            if existing is not None and existing.id != node.id:
                raise ValidationError("A node with this name already exists")
            node.node_name = updates["node_name"].strip()

        if "election_type" in updates:
            node.election_type = election_type

        if "house_id" in updates or "election_type" in updates:
            self._validate_house_assignment(election_type, house_id)
            node.house_id = house_id if election_type == ElectionType.HOUSE else None

        if "active" in updates:
            node.active = updates["active"]

        self._audit(
            user_id,
            "Node Assignment Updated",
            {
                "node_id": node.id,
                "node_name": node.node_name,
                "election_type": node.election_type.value,
                "house_id": node.house_id,
                "active": node.active,
            },
        )
        self.node_repository.commit()
        return self._to_assignment_response(node)

    def delete_node(self, node_id: str, *, user_id: str | None = None) -> None:
        """Deactivate a node and free its name so it can be re-registered."""
        node = self._get_node_or_raise(node_id)
        self._ensure_nodes_editable()

        if not node.active:
            raise ValidationError("Node is already deleted")

        original_name = node.node_name
        node.active = False
        # Keep within VARCHAR(100) while freeing the unique node_name constraint.
        suffix = f"__del__{node.id[:8]}"
        max_base = 100 - len(suffix)
        node.node_name = f"{original_name[:max_base]}{suffix}"

        self._audit(
            user_id,
            "Node Deleted",
            {
                "node_id": node.id,
                "node_name": original_name,
                "election_type": node.election_type.value,
                "house_id": node.house_id,
            },
        )
        self.node_repository.commit()

    def record_heartbeat(
        self,
        payload: HeartbeatRequest,
        *,
        ip_address: str | None = None,
    ) -> tuple[HeartbeatResponse, str, str]:
        """Record heartbeat and return response with previous/new node status."""
        node = self._get_node_or_raise(payload.node_id)
        if not node.active:
            raise ForbiddenError("Node is disabled")

        latest = self.heartbeat_repository.get_latest_for_node(node.id)
        previous_status = self._resolve_status(node, latest)

        now = utc_now()
        node.app_version = payload.app_version
        node.config_version = payload.config_version

        heartbeat = NodeHeartbeat(
            id=new_uuid(),
            node_id=node.id,
            heartbeat_time=now,
            queue_size=payload.queue_size,
            last_vote_time=payload.last_vote_time,
            sync_status=payload.sync_status,
            app_version=payload.app_version,
            config_version=payload.config_version,
            ip_address=ip_address,
        )
        self.heartbeat_repository.add(heartbeat)
        self.node_repository.commit()

        new_status = self._resolve_status(node, heartbeat)
        if previous_status != new_status:
            self._audit_status_change(
                node_id=node.id,
                node_name=node.node_name,
                previous_status=previous_status,
                new_status=new_status,
                ip_address=ip_address,
            )

        return (
            HeartbeatResponse(
                server_time=now,
                status=SyncStatus.HEALTHY.value,
                node_name=node.node_name,
            ),
            previous_status,
            new_status,
        )

    def get_node_health(self, node_id: str) -> NodeHealthResponse:
        node = self._get_node_or_raise(node_id)
        latest = self.heartbeat_repository.get_latest_for_node(node.id)
        status = self._resolve_status(node, latest)
        return NodeHealthResponse(
            node_id=node.id,
            node_name=node.node_name,
            status=status,
            last_heartbeat=latest.heartbeat_time if latest else None,
            queue_size=latest.queue_size if latest else 0,
            sync_status=latest.sync_status.value if latest else None,
            last_vote_time=latest.last_vote_time if latest else None,
            app_version=latest.app_version if latest else node.app_version,
            config_version=latest.config_version if latest else node.config_version,
        )

    def _validate_house_assignment(self, election_type: ElectionType, house_id: str | None) -> None:
        if election_type == ElectionType.HOUSE:
            if not house_id:
                raise ValidationError("House assignment is required for house voting nodes")
            house = self.house_repository.get_by_id(house_id)
            if house is None or not house.active:
                raise NotFoundError("House not found")
        elif house_id is not None:
            raise ValidationError("Regular voting nodes must not have a house assignment")

    def _ensure_nodes_editable(self) -> None:
        live_elections = self.election_repository.list_by_status(ElectionStatus.LIVE)
        if live_elections:
            raise ElectionLockedError("Cannot modify node assignments while an election is live")

    def _get_node_or_raise(self, node_id: str) -> VotingNode:
        node = self.node_repository.get_by_id(node_id)
        if node is None:
            raise NotFoundError("Node not found")
        return node

    def _resolve_status(self, node: VotingNode, latest: NodeHeartbeat | None) -> str:
        if not node.active:
            return "Disabled"
        if latest is None:
            return "Offline"
        threshold = timedelta(seconds=settings.websocket_timeout)
        heartbeat_at = latest.heartbeat_time
        if heartbeat_at.tzinfo is None:
            heartbeat_at = heartbeat_at.replace(tzinfo=timezone.utc)
        if utc_now() - heartbeat_at <= threshold:
            return "Online"
        return "Offline"

    def _to_response(self, node: VotingNode) -> NodeResponse:
        latest = self.heartbeat_repository.get_latest_for_node(node.id)
        status = self._resolve_status(node, latest)
        return NodeResponse(
            id=node.id,
            node_name=node.node_name,
            election_type=node.election_type.value,
            house_id=node.house_id,
            house_name=node.house.house_name if node.house else None,
            active=node.active,
            config_version=node.config_version,
            app_version=latest.app_version if latest else node.app_version,
            status=status,
            queue_size=latest.queue_size if latest else 0,
            sync_status=latest.sync_status.value if latest else None,
            last_heartbeat=latest.heartbeat_time if latest else None,
            last_vote_time=latest.last_vote_time if latest else None,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )

    def _to_assignment_response(self, node: VotingNode) -> NodeAssignmentResponse:
        return NodeAssignmentResponse(
            id=node.id,
            node_name=node.node_name,
            election_type=node.election_type.value,
            house_id=node.house_id,
            house_name=node.house.house_name if node.house else None,
            active=node.active,
            config_version=node.config_version,
        )

    def _audit(self, user_id: str | None, action: str, details: dict | None) -> None:
        if not user_id:
            return
        self.audit_log_repository.add(
            AuditLog(
                id=new_uuid(),
                user_id=user_id,
                module="Nodes",
                action=action,
                new_value=details,
            )
        )

    def _audit_status_change(
        self,
        *,
        node_id: str,
        node_name: str,
        previous_status: str,
        new_status: str,
        ip_address: str | None,
    ) -> None:
        self.audit_log_repository.add(
            AuditLog(
                id=new_uuid(),
                user_id=None,
                module="Nodes",
                action="Node Status Changed",
                old_value={"status": previous_status},
                new_value={
                    "status": new_status,
                    "node_id": node_id,
                    "node_name": node_name,
                },
                ip_address=ip_address,
            )
        )
