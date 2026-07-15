"""Election configuration download service."""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.data.election_store import ElectionStore
from app.services.api_client import APIClient


class ConfigService:
    """Download and manage local election configuration."""

    def __init__(self, api_client: APIClient, store: ElectionStore) -> None:
        self.api_client = api_client
        self.store = store

    def download_election(self, election_id: str, token: str | None = None) -> dict:
        headers = {"Authorization": f"Bearer {token}"} if token else None
        response = self.api_client.get(
            f"/api/v1/configuration/package?election_id={election_id}",
            headers=headers,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Download failed ({response.status_code}): {response.text}")

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
            temp_file.write(response.content)
            temp_path = Path(temp_file.name)

        try:
            result = self.store.install_config_package(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

        return result

    def get_local_summary(self) -> dict:
        data = self.store.data
        return {
            "election_id": data.get("election_id", ""),
            "version": data.get("election_version", 0),
            "positions": len(self.store.positions),
            "candidates": len(self.store.candidates),
            "last_download_at": data.get("last_download_at", ""),
        }
