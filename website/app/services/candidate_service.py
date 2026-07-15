"""Candidate API service for the administration website."""

from __future__ import annotations

from typing import Any

from nicegui import app

from app.dependencies.container import get_website_container


class CandidateService:
    """Website-side service for candidate management APIs."""

    @staticmethod
    def _auth_headers() -> dict[str, str]:
        token = app.storage.user.get("access_token")
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    @classmethod
    async def list_candidates(
        cls,
        *,
        election_id: str | None = None,
        election_type: str | None = None,
        house_id: str | None = None,
        search: str | None = None,
    ) -> tuple[bool, str, list[dict[str, Any]]]:
        params: dict[str, Any] = {}
        if election_id:
            params["election_id"] = election_id
        if election_type:
            params["election_type"] = election_type
        if house_id:
            params["house_id"] = house_id
        if search:
            params["search"] = search

        client = get_website_container().api_client
        response = await client.get("/candidates", params=params, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data or []

    @classmethod
    async def create_candidate(cls, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post("/candidates", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def update_candidate(
        cls,
        candidate_id: str,
        payload: dict[str, Any],
    ) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.put(f"/candidates/{candidate_id}", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def delete_candidate(cls, candidate_id: str) -> tuple[bool, str]:
        client = get_website_container().api_client
        response = await client.delete(f"/candidates/{candidate_id}", headers=cls._auth_headers())
        success, message, _ = client.parse_response(response)
        return success, message

    @classmethod
    async def upload_image(
        cls,
        candidate_id: str,
        *,
        filename: str,
        content: bytes,
        content_type: str,
        replace: bool = False,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        path = f"/candidates/{candidate_id}/image"
        files = {"file": (filename, content, content_type)}
        if replace:
            response = await client.put_multipart(path, files=files, headers=cls._auth_headers())
        else:
            response = await client.post_multipart(path, files=files, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def crop_image(
        cls,
        image_id: str,
        payload: dict[str, int],
    ) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post(f"/images/{image_id}/crop", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def rotate_image(
        cls,
        image_id: str,
        angle: int,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post(
            f"/images/{image_id}/rotate",
            json={"angle": angle},
            headers=cls._auth_headers(),
        )
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def zoom_image(
        cls,
        image_id: str,
        scale: float,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post(
            f"/images/{image_id}/zoom",
            json={"scale": scale},
            headers=cls._auth_headers(),
        )
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def reset_image(cls, image_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post(f"/images/{image_id}/reset", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def get_image_metadata(cls, image_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.get(f"/images/{image_id}/metadata", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def fetch_image_bytes(
        cls,
        image_id: str,
        *,
        variant: str = "processed",
    ) -> tuple[bool, str, bytes | None, str]:
        """Download an image variant as raw bytes for local editing.

        Returns (success, message, content, content_type).
        """
        client = get_website_container().api_client
        response = await client.download(
            f"/images/{image_id}",
            params={"variant": variant},
            headers=cls._auth_headers(),
        )
        if response.status_code != 200:
            return False, response.text or "Could not load image", None, "image/png"
        content_type = response.headers.get("content-type", "image/png")
        return True, "OK", response.content, content_type

    @classmethod
    async def fetch_image_data_url(
        cls,
        image_id: str,
        *,
        variant: str = "processed",
    ) -> tuple[bool, str, str | None]:
        """Download an image variant and return a data URL for browser preview."""
        import base64

        success, message, content, content_type = await cls.fetch_image_bytes(image_id, variant=variant)
        if not success or content is None:
            return False, message, None
        encoded = base64.b64encode(content).decode("ascii")
        return True, "OK", f"data:{content_type};base64,{encoded}"
