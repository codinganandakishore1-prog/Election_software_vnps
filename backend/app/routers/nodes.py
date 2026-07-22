"""Node management router."""

from election_platform.enums.admin import NotificationType
from election_platform.enums.election import ElectionType
from election_platform.enums.roles import UserRole
from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.dependencies.auth import AuthenticatedNodeId, CurrentUser, require_roles
from app.dependencies.providers import ServiceContainer
from app.schemas.house import NodeAssignmentResponse, NodeAssignmentUpdate
from app.schemas.node import (
    HeartbeatRequest,
    HeartbeatResponse,
    NodeCreate,
    NodeRegistrationResponse,
    NodeResponse,
)
from app.websocket.broadcaster import broadcast_heartbeat

router = APIRouter()

AdminUser = Depends(require_roles(UserRole.SUPER_ADMINISTRATOR, UserRole.ADMINISTRATOR))


@router.post("")
async def create_node(
    payload: NodeCreate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[NodeRegistrationResponse]:
    """Register a new voting node and return its one-time secret."""
    node = container.node_service.create_node(payload, user_id=current_user.id)
    return APIResponse.ok(message="Node registered successfully", data=node)


@router.post("/heartbeat")
async def node_heartbeat(
    payload: HeartbeatRequest,
    request: Request,
    node_id: AuthenticatedNodeId,
    container: ServiceContainer,
) -> APIResponse[HeartbeatResponse]:
    """Receive node heartbeat (voting node JWT required)."""
    if payload.node_id != node_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token does not match node",
        )
    client_ip = request.client.host if request.client else None
    result, previous_status, new_status = container.node_service.record_heartbeat(payload, ip_address=client_ip)

    health = container.node_service.get_node_health(payload.node_id)
    await broadcast_heartbeat(
        container,
        node_id=payload.node_id,
        node_name=health.node_name,
        status=health.status,
        queue_size=health.queue_size,
        sync_status=health.sync_status,
        config_version=health.config_version,
        last_vote_time=health.last_vote_time,
        last_heartbeat=health.last_heartbeat,
    )

    if previous_status != new_status:
        if new_status == "Offline":
            await container.notification_service.create_and_broadcast(
                title="Node offline",
                message=f"{health.node_name} is now offline.",
                notification_type=NotificationType.NODE_OFFLINE.value,
            )
        elif new_status == "Online" and previous_status in {"Offline", "Disabled"}:
            await container.notification_service.create_and_broadcast(
                title="Node online",
                message=f"{health.node_name} is back online.",
                notification_type=NotificationType.NODE_ONLINE.value,
            )

    return APIResponse.ok(data=result)


@router.get("")
async def list_nodes(
    current_user: CurrentUser,
    container: ServiceContainer,
    election_type: ElectionType | None = Query(default=None),
    house_id: str | None = Query(default=None),
    active_only: bool = Query(default=False),
) -> APIResponse[list[NodeResponse]]:
    """List all voting nodes."""
    _ = current_user
    nodes = container.node_service.list_nodes(
        election_type=election_type,
        house_id=house_id,
        active_only=active_only,
    )
    return APIResponse.ok(data=nodes)


@router.get("/{node_id}")
async def get_node(
    node_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[NodeResponse]:
    """Get node details."""
    _ = current_user
    node = container.node_service.get_node(node_id)
    return APIResponse.ok(data=node)


@router.put("/{node_id}")
async def update_node(
    node_id: str,
    payload: NodeAssignmentUpdate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[NodeAssignmentResponse]:
    """Update node name, election type, house assignment, or active status."""
    node = container.node_service.update_node_assignment(node_id, payload, user_id=current_user.id)
    return APIResponse.ok(message="Node updated successfully", data=node)


@router.delete("/{node_id}")
async def delete_node(
    node_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[None]:
    """Delete (deactivate) a voting node."""
    container.node_service.delete_node(node_id, user_id=current_user.id)
    return APIResponse.ok(message="Node deleted successfully")
