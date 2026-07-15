"""Theme and branding API service for the administration website."""

from __future__ import annotations

from typing import Any

from nicegui import app

from app.dependencies.container import get_website_container


class ThemeService:
    """Website-side service for theme management APIs."""

    ASSET_TYPES = (
        "school_logo",
        "election_logo",
        "background_light",
        "background_dark",
        "background_welcome",
        "icon_app",
        "icon_favicon",
    )

    @staticmethod
    def _auth_headers() -> dict[str, str]:
        token = app.storage.user.get("access_token")
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    @classmethod
    def asset_url(cls, theme_id: str, asset_type: str) -> str:
        """Build a backend URL for a theme asset (requires auth when fetched)."""
        client = get_website_container().api_client
        return client._url(f"/themes/{theme_id}/assets/{asset_type}")

    @classmethod
    async def list_themes(cls) -> tuple[bool, str, list[dict[str, Any]]]:
        client = get_website_container().api_client
        response = await client.get("/themes", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data or []

    @classmethod
    async def get_active_theme(cls) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.get("/themes/active", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def get_theme(cls, theme_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.get(f"/themes/{theme_id}", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def create_theme(cls, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post("/themes", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def update_theme(
        cls,
        theme_id: str,
        payload: dict[str, Any],
    ) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.put(f"/themes/{theme_id}", json=payload, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def delete_theme(cls, theme_id: str) -> tuple[bool, str]:
        client = get_website_container().api_client
        response = await client.delete(f"/themes/{theme_id}", headers=cls._auth_headers())
        success, message, _ = client.parse_response(response)
        return success, message

    @classmethod
    async def activate_theme(cls, theme_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post(f"/themes/{theme_id}/activate", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def upload_asset(
        cls,
        theme_id: str,
        asset_type: str,
        filename: str,
        content: bytes,
        content_type: str = "image/png",
    ) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post_multipart(
            f"/themes/{theme_id}/assets/{asset_type}",
            files={"file": (filename, content, content_type)},
            headers=cls._auth_headers(),
        )
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def prepare_download(cls, theme_id: str) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post(f"/themes/{theme_id}/download", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def download_package(cls, theme_id: str) -> tuple[bool, str, bytes | None, str]:
        client = get_website_container().api_client
        response = await client.download(
            f"/themes/{theme_id}/download/file",
            headers=cls._auth_headers(),
        )
        if response.status_code != 200:
            return False, response.text or "Download failed", None, ""
        filename = "theme_assets.zip"
        content_disposition = response.headers.get("content-disposition", "")
        if "filename=" in content_disposition:
            filename = content_disposition.split("filename=")[-1].strip('"')
        return True, "OK", response.content, filename
