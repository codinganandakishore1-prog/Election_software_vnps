"""Authentication router (placeholder)."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter

from app.schemas.auth import LoginRequest, NodeLoginRequest, TokenResponse

router = APIRouter()


@router.post("/login")
async def login(_payload: LoginRequest) -> APIResponse[TokenResponse]:
    """Authenticate website administrator."""
    raise NotImplementedError("Authentication not implemented in scaffold phase.")


@router.post("/logout")
async def logout() -> APIResponse[None]:
    """Invalidate current session."""
    return APIResponse.ok(message="Logout successful")


@router.post("/refresh")
async def refresh_token() -> APIResponse[dict]:
    """Refresh JWT access token."""
    raise NotImplementedError("Token refresh not implemented in scaffold phase.")


@router.post("/node-login")
async def node_login(_payload: NodeLoginRequest) -> APIResponse[TokenResponse]:
    """Authenticate voting node."""
    raise NotImplementedError("Node authentication not implemented in scaffold phase.")


@router.post("/verify")
async def verify_token() -> APIResponse[dict]:
    """Verify JWT validity."""
    return APIResponse.ok(data={"valid": True})
