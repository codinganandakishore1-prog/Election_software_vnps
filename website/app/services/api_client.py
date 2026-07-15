"""Backend API client."""

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

    async def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(
                self._url(path),
                params=params,
                headers=self._headers(headers),
            )

    async def post(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.post(
                self._url(path),
                json=json,
                headers=self._headers(headers),
            )

    async def put(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.put(
                self._url(path),
                json=json,
                headers=self._headers(headers),
            )

    async def patch(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.patch(
                self._url(path),
                json=json,
                headers=self._headers(headers),
            )

    async def delete(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.delete(
                self._url(path),
                headers=self._headers(headers),
            )

    async def post_multipart(
        self,
        path: str,
        *,
        files: dict[str, tuple[str, bytes, str]],
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.post(
                self._url(path),
                files=files,
                headers=self._headers(headers),
            )

    async def put_multipart(
        self,
        path: str,
        *,
        files: dict[str, tuple[str, bytes, str]],
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.put(
                self._url(path),
                files=files,
                headers=self._headers(headers),
            )

    async def download(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(
                self._url(path),
                params=params,
                headers=self._headers(headers),
            )

    @staticmethod
    def parse_response(response: httpx.Response) -> tuple[bool, str, Any]:
        """Return (success, message, data) from an API envelope."""
        try:
            payload = response.json()
        except ValueError:
            return False, response.text or "Unexpected response from server", None

        if isinstance(payload, dict) and "success" in payload:
            return payload.get("success", False), payload.get("message", ""), payload.get("data")

        if response.is_success:
            return True, "OK", payload
        detail = payload.get("detail") if isinstance(payload, dict) else str(payload)
        return False, str(detail or "Request failed"), None
