"""Local election configuration and display preferences."""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path

from election_platform.utils.checksum import CHECKSUM_FILENAME, compute_directory_checksum

DEFAULT_DISPLAY_SETTINGS = {
    "password": "1234",
    "background_path_light": "assets/backgrounds/default_light_bg.png",
    "background_path_dark": "assets/backgrounds/default_dark_bg.png",
    "image_size": 140,
    "image_spacing": 20,
    "font_family": "Arial",
    "text_size": 16,
    "aspect_ratio_fix": False,
    "show_voting_popup": True,
    "play_voting_sound": True,
    "show_popup_images": True,
    "show_image_borders": True,
    "font_color": "#FFFFFF",
    "node_id": "",
    "node_secret": "",
    "website_url": "http://localhost:8000",
    "election_id": "",
    "election_version": 0,
    "last_download_at": "",
}

DEFAULT_ELECTION_DATA = {
    **DEFAULT_DISPLAY_SETTINGS,
    "positions": ["SPL", "ASPL"],
    "candidates": [],
}


class ElectionStore:
    """Persist display preferences and downloaded election content."""

    def __init__(self, base_dir: Path, data_dir: Path | None = None) -> None:
        self.base_dir = base_dir
        self.data_dir = data_dir or (base_dir / "data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data_file = self.data_dir / "election_data.json"
        self.config_dir = self.data_dir / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.image_dir = self.data_dir / "candidate_images"
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        if not self.data_file.exists():
            self._data = dict(DEFAULT_ELECTION_DATA)
            self.save()
            return self._data
        try:
            with open(self.data_file, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            data = dict(DEFAULT_ELECTION_DATA)
        for key, value in DEFAULT_ELECTION_DATA.items():
            data.setdefault(key, value)
        self._data = data
        return data

    @property
    def data(self) -> dict:
        return self._data

    def save(self) -> None:
        with open(self.data_file, "w", encoding="utf-8") as handle:
            json.dump(self._data, handle, indent=4)

    def update(self, **fields: object) -> None:
        self._data.update(fields)
        self.save()

    @property
    def positions(self) -> list[str]:
        return list(self._data.get("positions", []))

    @property
    def candidates(self) -> list[dict]:
        return list(self._data.get("candidates", []))

    @property
    def position_catalog(self) -> list[dict]:
        return list(self._data.get("position_catalog", []))

    def resolve_position_id(self, candidate_data: dict) -> str:
        position_id = candidate_data.get("position_id", "")
        if position_id:
            return str(position_id)
        position_name = candidate_data.get("position", "")
        for position in self.position_catalog:
            if position.get("name") == position_name:
                return str(position.get("id", ""))
        return ""

    def resolve_election_type(self, candidate_data: dict) -> str:
        election_type = candidate_data.get("election_type")
        if election_type:
            return str(election_type)
        position_id = self.resolve_position_id(candidate_data)
        for position in self.position_catalog:
            if position.get("id") == position_id:
                return str(position.get("election_type", "Regular"))
        return "Regular"

    @staticmethod
    def _resolve_position_name(position_catalog: list[dict], position_id: str) -> str:
        for position in position_catalog:
            if position.get("id") == position_id:
                return str(position.get("name", ""))
        return ""

    def resolve_path(self, path: str) -> str:
        if not path:
            return ""
        if os.path.isabs(path) and os.path.exists(path):
            return path
        for candidate in (
            path,
            str(self.base_dir / path),
            str(self.config_dir / path),
            str(self.image_dir / path),
        ):
            if os.path.exists(candidate):
                return candidate
        return path

    def install_config_package(self, zip_path: str | Path) -> dict:
        """Extract and load a published configuration package."""
        zip_path = Path(zip_path)
        staging = self.config_dir / "_staging"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)

        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(staging)

        checksum_file = staging / CHECKSUM_FILENAME
        if checksum_file.exists():
            expected = checksum_file.read_text(encoding="utf-8").strip()
            actual = compute_directory_checksum(staging)
            if expected.lower() != actual.lower():
                shutil.rmtree(staging)
                raise ValueError("Configuration package checksum mismatch")

        election_data = self._read_json(staging / "Election.json")
        positions_data = self._read_json(staging / "Positions.json", default=[])
        candidates_data = self._read_json(staging / "Candidates.json", default=[])

        if staging.exists():
            for item in self.config_dir.iterdir():
                if item.name != "_staging":
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            for item in staging.iterdir():
                dest = self.config_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
            shutil.rmtree(staging)

        position_catalog: list[dict] = []
        positions: list[str] = []
        for item in positions_data:
            if not isinstance(item, dict):
                continue
            position_name = item.get("position_name") or item.get("name") or item.get("title") or item.get("code", "")
            if not position_name:
                continue
            position_catalog.append(
                {
                    "id": item.get("id", ""),
                    "name": position_name,
                    "election_type": item.get("election_type", "Regular"),
                }
            )
            positions.append(position_name)

        candidates: list[dict] = []
        for item in candidates_data:
            if not isinstance(item, dict):
                continue
            image_path = item.get("image_path") or item.get("photo_path") or item.get("image_file") or ""
            if image_path and not os.path.isabs(image_path):
                image_path = str(self.config_dir / image_path)
            position_name = item.get("position_name") or item.get("position", "")
            if not position_name and item.get("position_id"):
                position_name = self._resolve_position_name(position_catalog, item["position_id"])
            candidates.append(
                {
                    "id": item.get("id", ""),
                    "name": item.get("candidate_name") or item.get("name", "Unknown"),
                    "position": position_name,
                    "position_id": item.get("position_id", ""),
                    "house_id": item.get("house_id"),
                    "election_type": item.get("election_type"),
                    "candidate_class": str(item.get("class") or item.get("candidate_class", "")),
                    "candidate_section": str(item.get("section") or item.get("candidate_section", "")),
                    "image_path": image_path,
                }
            )

        self._data["position_catalog"] = position_catalog or self._data.get("position_catalog", [])
        self._data["positions"] = positions or self._data.get("positions", [])
        self._data["candidates"] = candidates
        self._data["election_id"] = election_data.get("id", "")
        self._data["election_version"] = election_data.get("version", 0)
        self.save()
        return {
            "election_id": self._data["election_id"],
            "version": self._data["election_version"],
            "positions": len(positions),
            "candidates": len(candidates),
        }

    @staticmethod
    def _read_json(path: Path, default: dict | list | None = None):
        if not path.exists():
            return default if default is not None else {}
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
