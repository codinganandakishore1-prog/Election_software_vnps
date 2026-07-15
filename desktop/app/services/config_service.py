"""Election configuration download service."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from app.data.election_store import ElectionStore
from app.services.api_client import APIClient, APIClientError

if TYPE_CHECKING:
    from app.sync.node_auth import NodeAuthenticator


class ConfigService:
    """Download and manage local election configuration."""

    def __init__(
        self,
        api_client: APIClient,
        store: ElectionStore,
        node_authenticator: NodeAuthenticator | None = None,
    ) -> None:
        self.api_client = api_client
        self.store = store
        self.node_authenticator = node_authenticator

    def download_election(self, election_id: str, token: str | None = None) -> dict:
        headers = self._auth_headers(token)
        response = self.api_client.get(
            f"/api/v1/configuration/package?election_id={election_id}",
            headers=headers,
        )
        if response.status_code == 401:
            # Token may have expired — re-login once with node credentials when available.
            if not token and self.node_authenticator and self.node_authenticator.has_credentials:
                self.node_authenticator.invalidate()
                headers = self.node_authenticator.auth_headers()
                response = self.api_client.get(
                    f"/api/v1/configuration/package?election_id={election_id}",
                    headers=headers,
                )
        if response.status_code != 200:
            detail = response.text
            try:
                payload = response.json()
                detail = payload.get("message") or payload.get("detail") or detail
            except Exception:
                pass
            raise RuntimeError(f"Download failed ({response.status_code}): {detail}")

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
            temp_file.write(response.content)
            temp_path = Path(temp_file.name)

        try:
            result = self.store.install_config_package(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

        return result

    def _auth_headers(self, token: str | None) -> dict[str, str]:
        if token:
            return {"Authorization": f"Bearer {token}"}
        if self.node_authenticator and self.node_authenticator.has_credentials:
            try:
                return self.node_authenticator.auth_headers()
            except APIClientError as exc:
                raise RuntimeError(
                    f"Could not authenticate node for download: {exc}. "
                    "Check Node ID / Node Secret under Admin → Node Configuration."
                ) from exc
        raise RuntimeError(
            "Authentication required to download. "
            "Save Node ID and Node Secret in Admin → Node Configuration, "
            "or paste a valid access token."
        )

    def get_local_summary(self) -> dict:
        data = self.store.data
        return {
            "election_id": data.get("election_id", ""),
            "version": data.get("election_version", 0),
            "positions": len(self.store.positions),
            "candidates": len(self.store.candidates),
            "last_download_at": data.get("last_download_at", ""),
        }
