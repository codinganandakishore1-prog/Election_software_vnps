"""Authentication router."""

from election_platform.enums.admin import NotificationType
from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, Request

from app.dependencies.auth import CurrentUser
from app.dependencies.providers import ServiceContainer
from app.schemas.auth import (
    LoginRequest,
    NodeLoginRequest,
    RefreshRequest,
    RefreshResponse,
    TokenResponse,
    VerifyResponse,
)

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _client_browser(request: Request) -> str | None:
    return request.headers.get("User-Agent")


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    container: ServiceContainer,
) -> APIResponse[TokenResponse]:
    """Authenticate website administrator."""
    result = container.auth_service.login(
        payload.username,
        payload.password,
        ip_address=_client_ip(request),
        browser=_client_browser(request),
    )
    await container.notification_service.create_and_broadcast(
        title="Administrator login",
        message=f"{payload.username} signed in to the administration portal.",
        notification_type=NotificationType.ADMIN_ACTION.value,
    )
    return APIResponse.ok(message="Login successful", data=result)


@router.post("/logout")
async def logout(
    request: Request,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[None]:
    """Invalidate current session."""
    session_id = None
    claims = getattr(request.state, "auth_claims", None)
    if isinstance(claims, dict):
        session_id = claims.get("sid")

    container.auth_service.logout(
        current_user,
        session_id=session_id,
        ip_address=_client_ip(request),
        browser=_client_browser(request),
    )
    return APIResponse.ok(message="Logout successful")


@router.post("/refresh")
async def refresh_token(
    payload: RefreshRequest,
    container: ServiceContainer,
) -> APIResponse[RefreshResponse]:
    """Refresh JWT access token."""
    result = container.auth_service.refresh(payload.refresh_token)
    return APIResponse.ok(message="Token refreshed", data=result)


@router.post("/node-login")
async def node_login(
    payload: NodeLoginRequest,
    container: ServiceContainer,
) -> APIResponse[TokenResponse]:
    """Authenticate voting node."""
    result = container.auth_service.node_login(payload.node_id, payload.node_secret)
    return APIResponse.ok(message="Node login successful", data=result)


@router.post("/verify")
async def verify_token(
    request: Request,
    container: ServiceContainer,
) -> APIResponse[VerifyResponse]:
    """Verify JWT validity."""
    authorization = request.headers.get("Authorization", "")
    if not authorization.lower().startswith("bearer "):
        return APIResponse.ok(data=VerifyResponse(valid=False))

    token = authorization.split(" ", 1)[1].strip()
    result = container.auth_service.verify(token)
    return APIResponse.ok(data=result)
