"""Request logging middleware."""

import time

from election_platform.logging.setup import get_logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = get_logger("backend.application")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log request method, path, and duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("%s %s -> %s (%.2f ms)", request.method, request.url.path, response.status_code, duration_ms)
        return response
