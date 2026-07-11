"""Vote synchronization router (placeholder)."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter

from app.schemas.sync import SyncResponse, VoteUploadRequest

router = APIRouter()


@router.post("/votes")
async def upload_votes(_payload: VoteUploadRequest) -> APIResponse[SyncResponse]:
    """Upload vote batch from voting node."""
    raise NotImplementedError("Vote synchronization not implemented in scaffold phase.")


@router.get("/version")
async def get_sync_version() -> APIResponse[dict]:
    """Check configuration version."""
    return APIResponse.ok(data={"latest_version": 0, "download_required": False})
