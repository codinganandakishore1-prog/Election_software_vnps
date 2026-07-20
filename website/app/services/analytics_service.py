"""Analytics API client."""

from __future__ import annotations

from typing import Any

from app.dependencies.container import get_website_container
from app.services.auth_service import AuthService


class AnalyticsService:
    """Fetch dashboard and live results from the backend."""

    @staticmethod
    def _auth_headers() -> dict[str, str]:
        token = AuthService.get_access_token()
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    async def _get(
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        client = get_website_container().api_client
        response = await client.get(path, headers=AnalyticsService._auth_headers(), params=params)
        success, message, data = client.parse_response(response)
        if success and isinstance(data, dict):
            return True, message, data
        return False, message or "Could not load analytics", None

    @staticmethod
    async def get_dashboard() -> dict[str, Any] | None:
        success, _, data = await AnalyticsService._get("/analytics/dashboard")
        return data if success else None

    @staticmethod
    async def get_live_results(election_id: str | None = None) -> dict[str, Any] | None:
        params = {"election_id": election_id} if election_id else None
        success, _, data = await AnalyticsService._get("/analytics/live", params=params)
        return data if success else None

    @staticmethod
    async def get_overview(
        election_id: str | None = None,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        params = {"election_id": election_id} if election_id else None
        return await AnalyticsService._get("/analytics", params=params)

    @staticmethod
    async def get_regular(election_id: str | None = None) -> dict[str, Any] | None:
        params = {"election_id": election_id} if election_id else None
        success, _, data = await AnalyticsService._get("/analytics/regular", params=params)
        return data if success else None

    @staticmethod
    async def get_houses(election_id: str | None = None) -> dict[str, Any] | None:
        params = {"election_id": election_id} if election_id else None
        success, _, data = await AnalyticsService._get("/analytics/houses", params=params)
        return data if success else None

    @staticmethod
    async def get_nodes(election_id: str | None = None) -> dict[str, Any] | None:
        params = {"election_id": election_id} if election_id else None
        success, _, data = await AnalyticsService._get("/analytics/nodes", params=params)
        return data if success else None

    @staticmethod
    async def get_timeline(
        election_id: str | None = None,
        *,
        interval: str = "minute",
        window: int = 30,
    ) -> dict[str, Any] | None:
        params: dict[str, Any] = {"interval": interval, "window": window}
        if election_id:
            params["election_id"] = election_id
        success, _, data = await AnalyticsService._get("/analytics/timeline", params=params)
        return data if success else None
