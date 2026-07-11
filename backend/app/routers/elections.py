"""Election management router (placeholder)."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter

from app.schemas.election import ElectionCreate, ElectionResponse

router = APIRouter()


@router.get("")
async def list_elections() -> APIResponse[list[ElectionResponse]]:
    """List all elections."""
    return APIResponse.ok(data=[])


@router.get("/{election_id}")
async def get_election(election_id: str) -> APIResponse[dict]:
    """Get election details."""
    return APIResponse.ok(data={"id": election_id})


@router.post("")
async def create_election(_payload: ElectionCreate) -> APIResponse[dict]:
    """Create a new election."""
    raise NotImplementedError("Election creation not implemented in scaffold phase.")


@router.post("/{election_id}/publish")
async def publish_election(election_id: str) -> APIResponse[dict]:
    """Publish election configuration."""
    raise NotImplementedError("Election publishing not implemented in scaffold phase.")


@router.post("/{election_id}/start")
async def start_election(election_id: str) -> APIResponse[dict]:
    """Start live voting."""
    return APIResponse.ok(message=f"Start election {election_id} (placeholder)")


@router.post("/{election_id}/end")
async def end_election(election_id: str) -> APIResponse[dict]:
    """End live voting."""
    return APIResponse.ok(message=f"End election {election_id} (placeholder)")
