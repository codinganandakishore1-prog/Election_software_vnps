"""Node JWT authentication for synchronization uploads."""

from __future__ import annotations

from election_platform.logging.setup import get_logger

from app.services.api_client import APIClient, APIClientError

logger = get_logger("desktop.sync")


class NodeAuthenticator:
    """Manage node JWT lifecycle for authenticated sync uploads."""

    def __init__(
        self,
        api_client: APIClient,
        node_id: str,
        node_secret: str,
        login_path: str = "/api/v1/auth/node-login",
    ) -> None:
        self.api_client = api_client
        self.node_id = node_id
        self.node_secret = node_secret
        self.login_path = login_path
        self._access_token: str | None = None

    @property
    def has_credentials(self) -> bool:
        return bool(self.node_id and self.node_secret)

    def auth_headers(self) -> dict[str, str]:
        """Return bearer authorization headers, logging in when required."""
        if not self.has_credentials:
            raise APIClientError("Node credentials are not configured")
        if self._access_token is None:
            self.login()
        return {"Authorization": f"Bearer {self._access_token}"}

    def login(self) -> str:
        """Authenticate the node and cache the access token."""
        response = self.api_client.post(
            self.login_path,
            json={"node_id": self.node_id, "node_secret": self.node_secret},
        )
        if response.status_code != 200:
            raise APIClientError(
                f"Node login failed with status {response.status_code}",
                status_code=response.status_code,
            )

        body = response.json()
        if not body.get("success"):
            raise APIClientError(body.get("message", "Node login failed"))

        data = body.get("data") or {}
        token = data.get("access_token")
        if not token:
            raise APIClientError("Node login response missing access token")

        self._access_token = token
        logger.info("Node authenticated for synchronization")
        return token

    def invalidate(self) -> None:
        """Clear the cached token after authentication failures."""
        self._access_token = None
