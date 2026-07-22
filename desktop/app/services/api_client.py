"""Backend API client for desktop synchronization."""

from __future__ import annotations

import requests
from requests import RequestException


class APIClientError(Exception):
    """Raised when an API request fails."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class APIClient:
    """HTTP client for website/backend communication."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get(self, path: str, headers: dict | None = None) -> requests.Response:
        return self._request("GET", path, headers=headers)

    def post(
        self,
        path: str,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> requests.Response:
        return self._request("POST", path, json=json, headers=headers)

    def is_reachable(self) -> bool:
        """Return True when the backend health endpoint responds."""
        try:
            response = self.get("/health")
            return response.status_code == 200
        except RequestException:
            return False

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> requests.Response:
        try:
            return requests.request(
                method,
                f"{self.base_url}{path}",
                json=json,
                headers=headers,
                timeout=self.timeout,
            )
        except RequestException as exc:
            raise APIClientError(f"Network error: {exc}") from exc
