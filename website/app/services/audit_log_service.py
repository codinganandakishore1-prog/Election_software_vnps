"""Audit log API client for the administration website."""

from __future__ import annotations

from typing import Any

from nicegui import app

from app.dependencies.container import get_website_container


class AuditLogService:
    """Website-side service for audit log APIs."""

    @staticmethod
    def _auth_headers() -> dict[str, str]:
        token = app.storage.user.get("access_token")
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    @classmethod
    async def list_audit_logs(
        cls,
        *,
        module: str | None = None,
        search: str | None = None,
        action: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if module and module != "all":
            params["module"] = module
        if search:
            params["search"] = search
        if action:
            params["action"] = action

        client = get_website_container().api_client
        response = await client.get("/audit-logs", params=params, headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        return success, message, data

    @classmethod
    async def list_modules(cls) -> tuple[bool, str, list[str]]:
        client = get_website_container().api_client
        response = await client.get("/audit-logs/modules", headers=cls._auth_headers())
        success, message, data = client.parse_response(response)
        if success and isinstance(data, list):
            return success, message, data
        return success, message, []
