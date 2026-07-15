"""CSRF protection middleware for browser-originated API requests."""

from __future__ import annotations

from urllib.parse import urlparse

from election_platform.logging.setup import get_logger
from election_platform.schemas.response import APIResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config.settings import settings

logger = get_logger("backend.security")

STATE_CHANGING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class CSRFMiddleware(BaseHTTPMiddleware):
    """Validate Origin/Referer headers for state-changing API requests."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in STATE_CHANGING_METHODS:
            return await call_next(request)

        path = request.url.path
        if not path.startswith(settings.api_prefix):
            return await call_next(request)

        if path.endswith("/auth/login") or path.endswith("/auth/node-login"):
            return await call_next(request)

        if request.headers.get("Authorization", "").lower().startswith("bearer "):
            return await call_next(request)

        if not self._origin_allowed(request):
            logger.warning("CSRF check failed for %s %s", request.method, path)
            return JSONResponse(
                status_code=403,
                content=APIResponse.fail(message="Cross-site request blocked").model_dump(),
            )

        return await call_next(request)

    def _origin_allowed(self, request: Request) -> bool:
        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if not origin:
            return settings.environment != "production"

        parsed = urlparse(origin)
        origin_host = parsed.netloc or parsed.path.split("/")[0]
        if not origin_host:
            return False

        allowed_hosts = {request.url.netloc, *self._configured_hosts()}
        return origin_host in allowed_hosts

    @staticmethod
    def _configured_hosts() -> set[str]:
        hosts: set[str] = set()
        for origin in settings.cors_origins:
            if origin == "*":
                continue
            parsed = urlparse(origin)
            if parsed.netloc:
                hosts.add(parsed.netloc)
        return hosts
