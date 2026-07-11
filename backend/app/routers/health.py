"""Health check router (placeholder)."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> APIResponse[dict]:
    """Public health endpoint."""
    return APIResponse.ok(message="Service is healthy", data={"status": "Healthy"})


@router.get("/health/database")
async def database_health() -> APIResponse[dict]:
    """Database connectivity check (placeholder)."""
    return APIResponse.ok(data={"connected": True})


@router.get("/health/websocket")
async def websocket_health() -> APIResponse[dict]:
    """WebSocket health check (placeholder)."""
    return APIResponse.ok(data={"connected_clients": 0})
