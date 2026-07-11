"""Analytics router (placeholder)."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard")
async def dashboard_analytics() -> APIResponse[dict]:
    """Return dashboard statistics."""
    return APIResponse.ok(data={"total_votes": 0, "online_nodes": 0})


@router.get("/regular")
async def regular_election_analytics() -> APIResponse[dict]:
    """Return regular election statistics."""
    return APIResponse.ok(data={})


@router.get("/houses")
async def house_election_analytics() -> APIResponse[dict]:
    """Return house election statistics."""
    return APIResponse.ok(data={})
