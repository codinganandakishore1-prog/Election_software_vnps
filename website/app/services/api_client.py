"""Backend API client (placeholder)."""

import httpx


class APIClient:
    """HTTP client for FastAPI backend communication."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get(self, path: str, headers: dict | None = None) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(f"{self.base_url}{path}", headers=headers)

    async def post(self, path: str, json: dict | None = None, headers: dict | None = None) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.post(f"{self.base_url}{path}", json=json, headers=headers)
