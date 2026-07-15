"""Authentication middleware for protected API routes."""

from election_platform.logging.setup import get_logger
from election_platform.schemas.response import APIResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config.settings import settings
from app.security.jwt import JWTHandler

logger = get_logger("backend.authentication")

PUBLIC_PATHS = frozenset(
    {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        f"{settings.api_prefix}/auth/login",
        f"{settings.api_prefix}/auth/refresh",
        f"{settings.api_prefix}/auth/node-login",
        f"{settings.api_prefix}/analytics/live",
    }
)
PUBLIC_PREFIXES = ("/health", "/ws/", "/static/")


class AuthMiddleware(BaseHTTPMiddleware):
    """Validate JWT tokens on protected API routes and attach claims to request state."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self.jwt_handler = JWTHandler()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if self._is_public_path(path):
            return await call_next(request)

        if not path.startswith(settings.api_prefix):
            return await call_next(request)

        authorization = request.headers.get("Authorization", "")
        if not authorization.lower().startswith("bearer "):
            logger.warning("Missing bearer token for %s %s", request.method, path)
            return self._unauthorized("Authentication required")

        token = authorization.split(" ", 1)[1].strip()
        payload = self.jwt_handler.decode_token_safe(token)
        if payload is None:
            logger.warning("Invalid JWT for %s %s", request.method, path)
            return self._unauthorized("Invalid or expired token")

        token_type = payload.get("type")
        if token_type not in {
            JWTHandler.TOKEN_TYPE_ACCESS,
            JWTHandler.TOKEN_TYPE_NODE,
        }:
            return self._unauthorized("Invalid token type")

        request.state.auth_claims = payload
        return await call_next(request)

    @staticmethod
    def _is_public_path(path: str) -> bool:
        if path in PUBLIC_PATHS:
            return True
        return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)

    @staticmethod
    def _unauthorized(message: str) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content=APIResponse.fail(message=message).model_dump(),
        )
