"""Rate limiting middleware."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from election_platform.logging.setup import get_logger
from election_platform.schemas.response import APIResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config.settings import settings

logger = get_logger("backend.security")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply sliding-window rate limits per client IP."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self._lock = Lock()
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        client_ip = self._client_ip(request)
        limit, window = self._limits_for_path(request.url.path)

        if not self._allow_request(client_ip, limit, window):
            logger.warning("Rate limit exceeded for %s on %s", client_ip, request.url.path)
            return JSONResponse(
                status_code=429,
                content=APIResponse.fail(message="Too many requests. Please try again later.").model_dump(),
            )

        return await call_next(request)

    def _limits_for_path(self, path: str) -> tuple[int, int]:
        # Keep the strict limit on interactive admin login only.
        # Node login uses the general API limit so voting machines behind one
        # school NAT are less likely to get false "Too many requests" errors.
        if path.endswith("/auth/login"):
            return settings.login_rate_limit_requests, settings.rate_limit_window_seconds
        return settings.rate_limit_requests, settings.rate_limit_window_seconds

    def _allow_request(self, client_ip: str, limit: int, window: int) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._requests[client_ip]
            while bucket and now - bucket[0] > window:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"
