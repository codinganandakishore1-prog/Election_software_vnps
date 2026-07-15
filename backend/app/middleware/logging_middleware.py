"""Request logging middleware."""

import time

from election_platform.logging.setup import get_logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = get_logger("backend.application")
error_logger = get_logger("backend.errors")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log request method, path, and duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            error_logger.exception(
                "%s %s failed after %.2f ms",
                request.method,
                request.url.path,
                duration_ms,
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        log = error_logger.warning if response.status_code >= 500 else logger.info
        log(
            "%s %s -> %s (%.2f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
