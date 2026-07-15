"""Authentication dependencies."""

from collections.abc import Callable
from typing import Annotated

from election_platform.enums.roles import UserRole
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.exceptions.base import AuthenticationError, ForbiddenError
from app.dependencies.providers import ServiceContainer
from app.models.user import User
from app.security.jwt import JWTHandler
from app.security.permissions import PermissionChecker

security_scheme = HTTPBearer(auto_error=False)


def _extract_bearer_token(
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return credentials.credentials


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    container: ServiceContainer,
) -> User:
    """Resolve the authenticated user from JWT and active session."""
    auth_context = getattr(request.state, "auth_user", None)
    if isinstance(auth_context, User):
        return auth_context

    token = _extract_bearer_token(credentials)
    try:
        user = container.auth_service.validate_access_token(token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message) from exc

    request.state.auth_user = user
    return user


async def get_optional_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    container: ServiceContainer,
) -> User | None:
    """Return the authenticated user when a valid token is supplied."""
    if credentials is None:
        return None
    try:
        return await get_current_user(request, credentials, container)
    except HTTPException:
        return None


def require_roles(*allowed_roles: UserRole) -> Callable:
    """FastAPI dependency factory that enforces role membership."""

    async def _check_role(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        role_name = current_user.role.role_name if current_user.role else ""
        if not PermissionChecker.has_role(role_name, list(allowed_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _check_role


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def get_authenticated_node_id(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
) -> str:
    """Resolve the authenticated voting node ID from a node JWT."""
    auth_claims = getattr(request.state, "auth_claims", None)
    if auth_claims is None:
        token = _extract_bearer_token(credentials)
        payload = JWTHandler().decode_token_safe(token)
        if payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        auth_claims = payload

    if auth_claims.get("type") != JWTHandler.TOKEN_TYPE_NODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voting node token required",
        )

    node_id = auth_claims.get("sub")
    if not node_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    return node_id


AuthenticatedNodeId = Annotated[str, Depends(get_authenticated_node_id)]
