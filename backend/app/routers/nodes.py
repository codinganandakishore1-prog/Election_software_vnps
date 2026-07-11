"""Node management router (placeholder)."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter

from app.schemas.node import HeartbeatRequest, NodeResponse

router = APIRouter()


@router.post("/heartbeat")
async def node_heartbeat(_payload: HeartbeatRequest) -> APIResponse[dict]:
    """Receive node heartbeat."""
    return APIResponse.ok(data={"status": "Healthy"})


@router.get("")
async def list_nodes() -> APIResponse[list[NodeResponse]]:
    """List all voting nodes."""
    return APIResponse.ok(data=[])


@router.get("/{node_id}")
async def get_node(node_id: str) -> APIResponse[dict]:
    """Get node details."""
    return APIResponse.ok(data={"id": node_id})
