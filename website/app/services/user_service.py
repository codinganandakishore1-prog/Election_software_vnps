"""User / profile API service for the administration website."""

from __future__ import annotations

from typing import Any

from nicegui import app

from app.dependencies.container import get_website_container


class UserService:
    """Website-side service for current-user profile APIs."""

    @staticmethod
    def _auth_headers() -> dict[str, str]:
        token = app.storage.user.get("access_token")
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    @classmethod
    async def get_me(cls) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.get("/users/me", headers=cls._auth_headers())
        return client.parse_response(response)

    @classmethod
    async def update_me(cls, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.put("/users/me", json=payload, headers=cls._auth_headers())
        return client.parse_response(response)

    @classmethod
    async def change_password(cls, old_password: str, new_password: str) -> tuple[bool, str, Any]:
        client = get_website_container().api_client
        response = await client.patch(
            "/users/change-password",
            json={"old_password": old_password, "new_password": new_password},
            headers=cls._auth_headers(),
        )
        return client.parse_response(response)
