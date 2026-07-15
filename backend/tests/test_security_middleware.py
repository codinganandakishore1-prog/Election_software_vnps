"""Security middleware tests."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from starlette.requests import Request
from starlette.responses import Response

from app.middleware.csrf import CSRFMiddleware
from app.middleware.rate_limit import RateLimitMiddleware


def test_rate_limit_blocks_excess_requests(monkeypatch) -> None:
    monkeypatch.setattr("app.middleware.rate_limit.settings.login_rate_limit_requests", 2)
    monkeypatch.setattr("app.middleware.rate_limit.settings.rate_limit_window_seconds", 60)

    middleware = RateLimitMiddleware(MagicMock())
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/login",
            "headers": [],
            "client": ("127.0.0.1", 1234),
        }
    )
    call_next = AsyncMock(return_value=Response(status_code=200))

    assert asyncio.run(middleware.dispatch(request, call_next)).status_code == 200
    assert asyncio.run(middleware.dispatch(request, call_next)).status_code == 200
    blocked = asyncio.run(middleware.dispatch(request, call_next))
    assert blocked.status_code == 429


def test_csrf_allows_bearer_authenticated_requests() -> None:
    middleware = CSRFMiddleware(MagicMock())
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/elections",
            "headers": [(b"authorization", b"Bearer test-token")],
            "client": ("127.0.0.1", 1234),
        }
    )
    call_next = AsyncMock(return_value=Response(status_code=200))
    response = asyncio.run(middleware.dispatch(request, call_next))
    assert response.status_code == 200
