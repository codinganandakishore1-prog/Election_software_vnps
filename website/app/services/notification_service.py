"""Notification API client."""

from __future__ import annotations

from typing import Any

from app.dependencies.container import get_website_container
from app.services.auth_service import AuthService


class NotificationService:
    """Fetch notifications from the backend."""

    @staticmethod
    def _auth_headers() -> dict[str, str]:
        token = AuthService.get_access_token()
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    async def list_recent() -> list[dict[str, Any]]:
        client = get_website_container().api_client
        response = await client.get("/notifications/recent", headers=NotificationService._auth_headers())
        success, _, data = client.parse_response(response)
        if success and isinstance(data, list):
            return data
        return []
