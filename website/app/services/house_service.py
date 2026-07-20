"""House management API service for the administration website."""

from __future__ import annotations

from typing import Any

from nicegui import app

from app.dependencies.container import get_website_container


class HouseService:
    """Website-side service for house management APIs."""

    @staticmethod
    def _auth_headers() -> dict[str, str]:
        token = app.storage.user.get("access_token")
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    @classmethod
    async def list_houses(cls) -> tuple[bool, str, list[dict[str, Any]]]:
        client = get_website_container().api_client
        response = await client.get("/houses", params={"details": True}, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data or []

    @classmethod
    async def get_configuration(cls, election_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.get(
            "/houses/configuration",
            params={"election_id": election_id},
            headers=cls._auth_headers(),
        )
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def configure_positions(
        cls,
        election_id: str,
        positions: list[str],
    ) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.put(
            "/houses/configuration",
            json={"election_id": election_id, "positions": positions},
            headers=cls._auth_headers(),
        )
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def validate(cls, election_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.get(
            "/houses/validate",
            params={"election_id": election_id},
            headers=cls._auth_headers(),
        )
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def list_candidates(
        cls,
        election_id: str,
        *,
        house_id: str | None = None,
    ) -> tuple[bool, str, list[dict[str, Any]]]:
        params: dict[str, Any] = {"election_id": election_id}
        if house_id:
            params["house_id"] = house_id
        client = get_website_container().api_client
        response = await client.get("/houses/candidates", params=params, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data or []

    @classmethod
    async def create_candidate(cls, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post("/houses/candidates", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def update_candidate(
        cls,
        candidate_id: str,
        payload: dict[str, Any],
    ) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.put(
            f"/houses/candidates/{candidate_id}",
            json=payload,
            headers=cls._auth_headers(),
        )
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def delete_candidate(cls, candidate_id: str) -> tuple[bool, str]:
        client = get_website_container().api_client
        response = await client.delete(f"/houses/candidates/{candidate_id}", headers=cls._auth_headers())
        success, message, _ = client.parse_response(response)
        return success, message

    @classmethod
    async def list_nodes(
        cls,
        *,
        election_type: str | None = None,
        house_id: str | None = None,
        active_only: bool = True,
    ) -> tuple[bool, str, list[dict[str, Any]]]:
        params: dict[str, Any] = {"active_only": active_only}
        if election_type:
            params["election_type"] = election_type
        if house_id:
            params["house_id"] = house_id
        client = get_website_container().api_client
        response = await client.get("/nodes", params=params, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data or []

    @classmethod
    async def create_node(cls, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post("/nodes", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def update_node(cls, node_id: str, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.put(f"/nodes/{node_id}", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def delete_node(cls, node_id: str) -> tuple[bool, str]:
        client = get_website_container().api_client
        response = await client.delete(f"/nodes/{node_id}", headers=cls._auth_headers())
        success, message, _ = client.parse_response(response)
        return success, message

    @classmethod
    async def list_elections(cls) -> tuple[bool, str, list[dict[str, Any]]]:
        client = get_website_container().api_client
        response = await client.get("/elections", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data or []
