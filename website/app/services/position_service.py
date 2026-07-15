"""Position API service for the administration website."""

from __future__ import annotations

from typing import Any

from nicegui import app

from app.dependencies.container import get_website_container


class PositionService:
    """Website-side service for position management APIs."""

    @staticmethod
    def _auth_headers() -> dict[str, str]:
        token = app.storage.user.get("access_token")
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    @classmethod
    async def list_positions(
        cls,
        *,
        election_id: str | None = None,
        election_type: str | None = None,
        search: str | None = None,
        active: bool | None = None,
    ) -> tuple[bool, str, list[dict[str, Any]]]:
        params: dict[str, Any] = {}
        if election_id:
            params["election_id"] = election_id
        if election_type:
            params["election_type"] = election_type
        if search:
            params["search"] = search
        if active is not None:
            params["active"] = active

        client = get_website_container().api_client
        response = await client.get("/positions", params=params, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data or []

    @classmethod
    async def create_position(cls, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post("/positions", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def update_position(
        cls,
        position_id: str,
        payload: dict[str, Any],
    ) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.put(f"/positions/{position_id}", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def delete_position(cls, position_id: str) -> tuple[bool, str]:
        client = get_website_container().api_client
        response = await client.delete(f"/positions/{position_id}", headers=cls._auth_headers())
        success, message, _ = client.parse_response(response)
        return success, message

    @classmethod
    async def enable_position(cls, position_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post(f"/positions/{position_id}/enable", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def disable_position(cls, position_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post(f"/positions/{position_id}/disable", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def move_position(cls, position_id: str, direction: str) -> tuple[bool, str, dict[str, Any] | None]:
        endpoint = "move-up" if direction == "up" else "move-down"
        client = get_website_container().api_client
        response = await client.post(f"/positions/{position_id}/{endpoint}", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def reorder_positions(cls, payload: dict[str, Any]) -> tuple[bool, str, list[dict[str, Any]]]:
        client = get_website_container().api_client
        response = await client.put("/positions/reorder", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data or []

    @classmethod
    async def list_elections(cls) -> tuple[bool, str, list[dict[str, Any]]]:
        client = get_website_container().api_client
        response = await client.get("/elections", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data or []
