"""User management router (placeholder)."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def get_current_user_profile() -> APIResponse[dict]:
    """Return current authenticated user."""
    raise NotImplementedError("User profile not implemented in scaffold phase.")


@router.get("")
async def list_users() -> APIResponse[list]:
    """List all users."""
    return APIResponse.ok(data=[])


@router.post("")
async def create_user() -> APIResponse[dict]:
    """Create a new user."""
    raise NotImplementedError("User creation not implemented in scaffold phase.")
