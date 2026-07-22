"""Backend API client with automatic JWT refresh on 401."""

from __future__ import annotations

from typing import Any

import httpx


class APIClient:
    """HTTP client for FastAPI backend communication."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.base_url}{path}"

    def _headers(self, headers: dict[str, str] | None = None) -> dict[str, str]:
        merged = {"Accept": "application/json"}
        if headers:
            merged.update(headers)
        return merged

    @staticmethod
    def _has_bearer(headers: dict[str, str] | None) -> bool:
        if not headers:
            return False
        auth = headers.get("Authorization") or headers.get("authorization") or ""
        return auth.lower().startswith("bearer ")

    async def _renew_auth_headers(self, headers: dict[str, str] | None) -> dict[str, str] | None:
        """Refresh the access token and rewrite Authorization if possible."""
        if not self._has_bearer(headers):
            return None
        from app.services.auth_service import AuthService

        if not await AuthService.refresh_access_token():
            return None
        renewed = dict(headers or {})
        token = AuthService.get_access_token()
        if not token:
            return None
        renewed["Authorization"] = f"Bearer {token}"
        return renewed

    async def _send(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
        headers: dict[str, str] | None = None,
        retry_auth: bool = True,
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method,
                self._url(path),
                params=params,
                json=json,
                files=files,
                headers=self._headers(headers),
            )

        if response.status_code != 401 or not retry_auth or not self._has_bearer(headers):
            return response

        renewed_headers = await self._renew_auth_headers(headers)
        if renewed_headers is None:
            return response

        return await self._send(
            method,
            path,
            params=params,
            json=json,
            files=files,
            headers=renewed_headers,
            retry_auth=False,
        )

    async def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return await self._send("GET", path, params=params, headers=headers)

    async def post(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return await self._send("POST", path, json=json, headers=headers)

    async def put(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return await self._send("PUT", path, json=json, headers=headers)

    async def patch(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return await self._send("PATCH", path, json=json, headers=headers)

    async def delete(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return await self._send("DELETE", path, headers=headers)

    async def post_multipart(
        self,
        path: str,
        *,
        files: dict[str, tuple[str, bytes, str]],
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return await self._send("POST", path, files=files, headers=headers)

    async def put_multipart(
        self,
        path: str,
        *,
        files: dict[str, tuple[str, bytes, str]],
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return await self._send("PUT", path, files=files, headers=headers)

    async def download(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return await self._send("GET", path, params=params, headers=headers)

    @staticmethod
    def parse_response(response: httpx.Response) -> tuple[bool, str, Any]:
        """Return (success, message, data) from an API envelope."""
        try:
            payload = response.json()
        except ValueError:
            return False, response.text or "Unexpected response from server", None

        if response.status_code == 401:
            detail = None
            if isinstance(payload, dict):
                detail = payload.get("detail") or payload.get("message")
            return False, str(detail or "Session expired. Please sign in again."), None

        if isinstance(payload, dict) and "success" in payload:
            return payload.get("success", False), payload.get("message", ""), payload.get("data")

        if response.is_success:
            return True, "OK", payload
        detail = payload.get("detail") if isinstance(payload, dict) else str(payload)
        return False, str(detail or "Request failed"), None
