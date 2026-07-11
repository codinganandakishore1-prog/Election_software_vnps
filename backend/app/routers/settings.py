"""Website settings router (placeholder)."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_settings() -> APIResponse[dict]:
    """Return website settings."""
    return APIResponse.ok(data={})


@router.put("")
async def update_settings() -> APIResponse[dict]:
    """Update website settings."""
    raise NotImplementedError("Settings update not implemented in scaffold phase.")


@router.get("/database")
async def get_database_settings() -> APIResponse[dict]:
    """Return MySQL configuration (masked)."""
    return APIResponse.ok(data={})


@router.post("/database/test")
async def test_database_connection() -> APIResponse[dict]:
    """Test MySQL connection."""
    return APIResponse.ok(data={"success": True})
