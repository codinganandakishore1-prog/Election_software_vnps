"""Position management router (placeholder)."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter

from app.schemas.position import PositionCreate, PositionResponse

router = APIRouter()


@router.get("")
async def list_positions() -> APIResponse[list[PositionResponse]]:
    """List all positions."""
    return APIResponse.ok(data=[])


@router.post("")
async def create_position(_payload: PositionCreate) -> APIResponse[dict]:
    """Create a new position."""
    raise NotImplementedError("Position creation not implemented in scaffold phase.")
