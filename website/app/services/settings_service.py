"""Website settings API service."""

from __future__ import annotations

from typing import Any

from nicegui import app

from app.dependencies.container import get_website_container


class SettingsService:
    """Website-side service for settings APIs."""

    @staticmethod
    def _auth_headers() -> dict[str, str]:
        token = app.storage.user.get("access_token")
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    @classmethod
    async def get_settings(cls) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.get("/settings", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def update_settings(cls, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.put("/settings", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def get_database_settings(cls) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.get("/settings/database", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def update_database_settings(cls, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.put("/settings/database", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def test_database_connection(cls, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post("/settings/database/test", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def test_saved_database_connection(cls) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post("/settings/database/test-saved", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data
