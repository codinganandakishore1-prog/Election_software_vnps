"""Rate limiting middleware."""

from __future__ import annotations

import hashlib
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

# Paths that must never be rate-limited (load balancers, health probes).
_EXEMPT_PREFIXES = ("/health", "/docs", "/openapi.json", "/redoc")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply sliding-window rate limits per client (user token or IP)."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self._lock = Lock()
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if any(path == prefix or path.startswith(prefix + "/") for prefix in _EXEMPT_PREFIXES):
            return await call_next(request)

        # RATE_LIMIT_REQUESTS=0 disables limiting (useful for trusted internal deploys).
        if settings.rate_limit_requests <= 0:
            return await call_next(request)

        client_key = self._client_key(request, path)
        limit, window = self._limits_for_path(path)

        if not self._allow_request(client_key, limit, window):
            logger.warning("Rate limit exceeded for %s on %s", client_key[:48], path)
            return JSONResponse(
                status_code=429,
                content=APIResponse.fail(message="Too many requests. Please try again later.").model_dump(),
            )

        return await call_next(request)

    def _limits_for_path(self, path: str) -> tuple[int, int]:
        # Strict limit only on interactive admin login (brute-force protection).
        # Node login and authenticated API traffic use the general high ceiling.
        if path.endswith("/auth/login"):
            return settings.login_rate_limit_requests, settings.rate_limit_window_seconds
        return settings.rate_limit_requests, settings.rate_limit_window_seconds

    def _allow_request(self, client_key: str, limit: int, window: int) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._requests[client_key]
            while bucket and now - bucket[0] > window:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True

    def _client_key(self, request: Request, path: str) -> str:
        """Prefer per-user/token buckets so a school NAT or website server IP
        is not shared across every admin and voting node."""
        # Login attempts stay IP-based (no token yet).
        if path.endswith("/auth/login"):
            return f"login:{self._client_ip(request)}"

        auth = request.headers.get("Authorization") or ""
        if auth.lower().startswith("bearer ") and len(auth) > 20:
            digest = hashlib.sha256(auth.encode("utf-8")).hexdigest()[:32]
            return f"tok:{digest}"

        return f"ip:{self._client_ip(request)}"

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"
