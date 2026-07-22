"""Vote synchronization router."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, Request

from app.dependencies.auth import AuthenticatedNodeId
from app.dependencies.providers import ServiceContainer
from app.schemas.sync import SyncResponse, SyncVersionResponse, VoteUploadRequest
from app.websocket.broadcaster import broadcast_sync_status, broadcast_vote_synced

router = APIRouter()


@router.post("/votes")
async def upload_votes(
    payload: VoteUploadRequest,
    request: Request,
    node_id: AuthenticatedNodeId,
    container: ServiceContainer,
) -> APIResponse[SyncResponse]:
    """Upload vote batch from voting node."""
    client_ip = request.client.host if request.client else None
    result = container.sync_service.upload_votes(
        payload,
        node_id,
        ip_address=client_ip,
    )

    node = container.node_repository.get_by_id(node_id)
    node_name = node.node_name if node else node_id

    if result.accepted:
        await broadcast_vote_synced(
            container,
            node_id=node_id,
            accepted_count=len(result.accepted),
            vote_uuids=result.accepted,
        )

    if result.failed:
        health = container.node_service.get_node_health(node_id)
        await broadcast_sync_status(
            container,
            node_id=node_id,
            node_name=node_name,
            sync_status="Failed",
            queue_size=health.queue_size,
            failed_count=len(result.failed),
        )
    elif result.accepted:
        await broadcast_sync_status(
            container,
            node_id=node_id,
            node_name=node_name,
            sync_status="Healthy",
            queue_size=0,
            failed_count=0,
        )

    return APIResponse.ok(
        message="Vote synchronization completed",
        data=result,
    )


@router.get("/version")
async def get_sync_version(
    node_id: AuthenticatedNodeId,
    container: ServiceContainer,
) -> APIResponse[SyncVersionResponse]:
    """Check configuration version for the authenticated node."""
    version = container.sync_service.get_sync_version(node_id)
    return APIResponse.ok(data=version)
