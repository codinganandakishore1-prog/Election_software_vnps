"""Backend API client for desktop (placeholder)."""

import requests


class APIClient:
    """HTTP client for website/backend communication."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get(self, path: str, headers: dict | None = None) -> requests.Response:
        return requests.get(f"{self.base_url}{path}", headers=headers, timeout=self.timeout)

    def post(self, path: str, json: dict | None = None, headers: dict | None = None) -> requests.Response:
        return requests.post(f"{self.base_url}{path}", json=json, headers=headers, timeout=self.timeout)
