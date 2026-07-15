"""Election API service for the administration website."""

from __future__ import annotations

from typing import Any

from nicegui import app

from app.dependencies.container import get_website_container


class ElectionService:
    """Website-side service for election management APIs."""

    @staticmethod
    def _auth_headers() -> dict[str, str]:
        token = app.storage.user.get("access_token")
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    @classmethod
    async def list_elections(
        cls,
        *,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[bool, str, list[dict[str, Any]]]:
        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        if search:
            params["search"] = search

        client = get_website_container().api_client
        response = await client.get("/elections", params=params, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data or []

    @classmethod
    async def get_election(cls, election_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.get(f"/elections/{election_id}", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def create_election(cls, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post("/elections", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def update_election(
        cls,
        election_id: str,
        payload: dict[str, Any],
    ) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.put(f"/elections/{election_id}", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def delete_election(cls, election_id: str) -> tuple[bool, str]:
        client = get_website_container().api_client
        response = await client.delete(f"/elections/{election_id}", headers=cls._auth_headers())
        success, message, _ = client.parse_response(response)
        return success, message

    @classmethod
    async def validate_election(cls, election_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.get(f"/elections/{election_id}/validate", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def publish_election(cls, election_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post(f"/elections/{election_id}/publish", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def lock_election(cls, election_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post(f"/elections/{election_id}/lock", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def unlock_election(cls, election_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post(f"/elections/{election_id}/unlock", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def archive_election(cls, election_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post(f"/elections/{election_id}/archive", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def duplicate_election(
        cls,
        election_id: str,
        *,
        name: str | None = None,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        payload = {"name": name} if name else {}
        client = get_website_container().api_client
        response = await client.post(
            f"/elections/{election_id}/duplicate",
            json=payload,
            headers=cls._auth_headers(),
        )
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def list_versions(cls, election_id: str) -> tuple[bool, str, list[dict[str, Any]]]:
        client = get_website_container().api_client
        response = await client.get(f"/elections/{election_id}/versions", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data or []

    @classmethod
    async def start_election(cls, election_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post(f"/elections/{election_id}/start", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def end_election(cls, election_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post(f"/elections/{election_id}/end", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data
