"""Report API service for the administration website."""

from __future__ import annotations

from typing import Any

from nicegui import app

from app.dependencies.container import get_website_container


class ReportService:
    """Website-side service for report generation and download."""

    @staticmethod
    def _auth_headers() -> dict[str, str]:
        token = app.storage.user.get("access_token")
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    @classmethod
    async def list_reports(
        cls,
        *,
        election_id: str | None = None,
        report_type: str | None = None,
    ) -> tuple[bool, str, list[dict[str, Any]]]:
        params: dict[str, Any] = {}
        if election_id:
            params["election_id"] = election_id
        if report_type:
            params["report_type"] = report_type

        client = get_website_container().api_client
        response = await client.get("/reports", params=params, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data or []

    @classmethod
    async def generate_report(
        cls,
        election_id: str,
        report_format: str,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.post(
            "/reports/generate",
            json={"election_id": election_id, "format": report_format},
            headers=cls._auth_headers(),
        )
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def download_report(cls, report_id: str) -> tuple[bool, str, bytes | None, str | None]:
        client = get_website_container().api_client
        response = await client.download(f"/reports/{report_id}/download", headers=cls._auth_headers())
        if response.is_success:
            content_type = response.headers.get("content-type", "application/octet-stream")
            return True, "Download ready", response.content, content_type
        success, message, _ = client.parse_response(response)
        return success, message or "Download failed", None, None

    @classmethod
    async def delete_report(cls, report_id: str) -> tuple[bool, str]:
        client = get_website_container().api_client
        response = await client.delete(f"/reports/{report_id}", headers=cls._auth_headers())
        success, message, _ = client.parse_response(response)
        return success, message or ("Report deleted" if success else "Delete failed")
