"""Election configuration package builder."""

from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from election_platform.utils.checksum import CHECKSUM_FILENAME, compute_directory_checksum

from app.config.settings import settings
from app.models.candidate import Candidate, CandidateImage
from app.models.election import Election
from app.models.house import House
from app.models.position import Position
from app.models.settings import SystemSettings, Theme
from app.repositories.candidate_repository import CandidateImageRepository, CandidateRepository
from app.repositories.election_repository import ElectionRepository
from app.repositories.house_repository import HouseRepository
from app.repositories.position_repository import PositionRepository
from app.repositories.settings_repository import SettingsRepository, ThemeRepository

# SRS configuration package layout (srs_files/05_Node_Synchronization.md §9)
PACKAGE_JSON_FILES = (
    "Election.json",
    "Candidates.json",
    "Positions.json",
    "Houses.json",
    "Settings.json",
    "Theme.json",
)
IMAGES_DIR = "Images"
LOGO_DIR = "Logo"


@dataclass
class ConfigPackageResult:
    """Result of building a configuration package."""

    package_path: str
    checksum: str
    package_size: int


class ConfigPackageService:
    """Builds versioned ZIP configuration packages for desktop nodes."""

    def __init__(
        self,
        election_repository: ElectionRepository,
        position_repository: PositionRepository,
        candidate_repository: CandidateRepository,
        candidate_image_repository: CandidateImageRepository,
        house_repository: HouseRepository,
        settings_repository: SettingsRepository,
        theme_repository: ThemeRepository,
    ) -> None:
        self.election_repository = election_repository
        self.position_repository = position_repository
        self.candidate_repository = candidate_repository
        self.candidate_image_repository = candidate_image_repository
        self.house_repository = house_repository
        self.settings_repository = settings_repository
        self.theme_repository = theme_repository

    def build_package(self, election: Election, version: int) -> ConfigPackageResult:
        """Build a configuration ZIP for the given election version."""
        package_dir = settings.config_package_folder / election.id / f"v{version}"
        package_dir.mkdir(parents=True, exist_ok=True)

        staging_dir = package_dir / "staging"
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        staging_dir.mkdir(parents=True)

        positions = self.position_repository.list_for_election(election.id, include_inactive=False)
        candidates = self.candidate_repository.list_for_election(election.id)
        houses = self.house_repository.list_all_ordered()
        system_settings = self.settings_repository.get_active()
        theme = self.theme_repository.get_active()

        election_data = self._serialize_election(election, version)
        positions_data = [self._serialize_position(position) for position in positions]
        candidates_data = [self._serialize_candidate(candidate) for candidate in candidates]
        houses_data = [self._serialize_house(house) for house in houses]
        settings_data = self._serialize_settings(system_settings)
        theme_data = self._serialize_theme(theme)

        self._write_json(staging_dir / "Election.json", election_data)
        self._write_json(staging_dir / "Positions.json", positions_data)
        self._write_json(staging_dir / "Candidates.json", candidates_data)
        self._write_json(staging_dir / "Houses.json", houses_data)
        self._write_json(staging_dir / "Settings.json", settings_data)
        self._write_json(staging_dir / "Theme.json", theme_data)

        images_dir = staging_dir / IMAGES_DIR
        images_dir.mkdir()
        logo_dir = staging_dir / LOGO_DIR
        logo_dir.mkdir()

        self._copy_candidate_images(candidates, images_dir)
        self._copy_election_logo(election, logo_dir)
        self._copy_house_logos(houses, logo_dir)
        self._copy_theme_assets(theme, logo_dir, images_dir)

        checksum = compute_directory_checksum(staging_dir)
        (staging_dir / CHECKSUM_FILENAME).write_text(checksum, encoding="utf-8")

        zip_path = package_dir / f"{election.id}_v{version}.zip"
        if zip_path.exists():
            zip_path.unlink()

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path in sorted(staging_dir.rglob("*")):
                if file_path.is_file():
                    archive.write(file_path, arcname=file_path.relative_to(staging_dir).as_posix())

        shutil.rmtree(staging_dir)

        return ConfigPackageResult(
            package_path=str(zip_path),
            checksum=checksum,
            package_size=zip_path.stat().st_size,
        )

    def _serialize_election(self, election: Election, version: int) -> dict[str, Any]:
        return {
            "id": election.id,
            "name": election.election_name,
            "academic_year": election.academic_year,
            "description": election.description,
            "version": version,
            "status": election.status.value,
            "start_time": self._iso(election.start_time),
            "end_time": self._iso(election.end_time),
            "logo_path": election.logo_path,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "checksum_algorithm": "SHA-256",
        }

    def _serialize_position(self, position: Position) -> dict[str, Any]:
        return {
            "id": position.id,
            "election_id": position.election_id,
            "election_type": position.election_type.value,
            "position_name": position.position_name,
            "winner_count": position.winner_count,
            "display_order": position.display_order,
        }

    def _serialize_candidate(self, candidate: Candidate) -> dict[str, Any]:
        image: CandidateImage | None = None
        if candidate.image_id:
            image = self.candidate_image_repository.get_by_id(candidate.image_id)

        return {
            "id": candidate.id,
            "election_id": candidate.election_id,
            "position_id": candidate.position_id,
            "house_id": candidate.house_id,
            "candidate_name": candidate.candidate_name,
            "class": candidate.candidate_class,
            "section": candidate.candidate_section,
            "candidate_class": candidate.candidate_class,
            "candidate_section": candidate.candidate_section,
            "display_order": candidate.display_order,
            "status": candidate.status.value,
            "image_file": self._package_image_name(candidate.id, image.processed_path) if image else None,
            "image_thumbnail": self._package_image_name(candidate.id, image.thumbnail_path, "_thumb")
            if image
            else None,
            "image_original": self._package_image_name(candidate.id, image.original_path, "_original")
            if image
            else None,
        }

    def _serialize_house(self, house: House) -> dict[str, Any]:
        logo_file: str | None = None
        if house.logo_path:
            source_path = self._resolve_upload_path(house.logo_path)
            if source_path is not None:
                logo_file = f"house_{house.id}{source_path.suffix}"

        return {
            "id": house.id,
            "house_name": house.house_name,
            "color": house.color,
            "logo_path": house.logo_path,
            "logo_file": logo_file,
        }

    def _serialize_settings(self, system_settings: SystemSettings | None) -> dict[str, Any]:
        if system_settings is None:
            return {}
        return {
            "school_name": system_settings.school_name,
            "school_logo": system_settings.school_logo,
            "election_logo": system_settings.election_logo,
            "primary_color": system_settings.primary_color,
            "secondary_color": system_settings.secondary_color,
            "timezone": system_settings.timezone,
        }

    def _serialize_theme(self, theme: Theme | None) -> dict[str, Any]:
        if theme is None:
            return {}
        return {
            "id": theme.id,
            "theme_name": theme.theme_name,
            "school_name": theme.school_name,
            "fonts": {
                "heading": theme.font_heading,
                "body": theme.font_body,
                "accent": theme.font_accent,
            },
            "colors": {
                "primary": theme.primary_color,
                "secondary": theme.secondary_color,
                "accent": theme.accent_color,
                "warning": theme.warning_color,
                "danger": theme.danger_color,
                "background": theme.background_color,
                "surface": theme.surface_color,
                "text_primary": theme.text_primary_color,
                "text_secondary": theme.text_secondary_color,
            },
            "assets": {
                "school_logo": f"{LOGO_DIR}/school_logo.png" if theme.school_logo_path else None,
                "election_logo": f"{LOGO_DIR}/election_logo.png" if theme.election_logo_path else None,
                "background_light": f"{IMAGES_DIR}/background_light.png" if theme.background_light_path else None,
                "background_dark": f"{IMAGES_DIR}/background_dark.png" if theme.background_dark_path else None,
                "background_welcome": f"{IMAGES_DIR}/background_welcome.png"
                if theme.background_welcome_path
                else None,
                "icon_app": f"{LOGO_DIR}/app_icon.png" if theme.icon_app_path else None,
                "icon_favicon": f"{LOGO_DIR}/favicon.png" if theme.icon_favicon_path else None,
            },
            "logo_path": theme.logo_path,
        }

    def _copy_theme_assets(
        self,
        theme: Theme | None,
        logo_dir: Path,
        images_dir: Path,
    ) -> None:
        if theme is None:
            return
        asset_map = [
            (theme.school_logo_path, logo_dir, "school_logo.png"),
            (theme.election_logo_path, logo_dir, "election_logo.png"),
            (theme.icon_app_path, logo_dir, "app_icon.png"),
            (theme.icon_favicon_path, logo_dir, "favicon.png"),
            (theme.background_light_path, images_dir, "background_light.png"),
            (theme.background_dark_path, images_dir, "background_dark.png"),
            (theme.background_welcome_path, images_dir, "background_welcome.png"),
        ]
        for relative_path, target_dir, filename in asset_map:
            if not relative_path:
                continue
            source_path = self._resolve_upload_path(relative_path)
            if source_path is None or not source_path.exists():
                continue
            shutil.copy2(source_path, target_dir / filename)

    def _copy_candidate_images(self, candidates: list[Candidate], images_dir: Path) -> None:
        for candidate in candidates:
            if not candidate.image_id:
                continue
            image = self.candidate_image_repository.get_by_id(candidate.image_id)
            if image is None:
                continue

            image_variants = [
                (image.processed_path, ""),
                (image.thumbnail_path, "_thumb"),
                (image.original_path, "_original"),
            ]
            for source_rel, suffix in image_variants:
                source_path = self._resolve_upload_path(source_rel)
                if source_path is None or not source_path.exists():
                    continue
                destination = images_dir / f"{candidate.id}{suffix}{source_path.suffix}"
                shutil.copy2(source_path, destination)

    def _copy_election_logo(self, election: Election, logo_dir: Path) -> None:
        if not election.logo_path:
            return
        source_path = self._resolve_upload_path(election.logo_path)
        if source_path is None or not source_path.exists():
            return
        shutil.copy2(source_path, logo_dir / f"election_{election.id}{source_path.suffix}")

    def _copy_house_logos(self, houses: list[House], logo_dir: Path) -> None:
        for house in houses:
            if not house.logo_path:
                continue
            source_path = self._resolve_upload_path(house.logo_path)
            if source_path is None or not source_path.exists():
                continue
            shutil.copy2(source_path, logo_dir / f"house_{house.id}{source_path.suffix}")

    def _package_image_name(self, candidate_id: str, path: str | None, suffix: str = "") -> str | None:
        if not path:
            return None
        return f"{candidate_id}{suffix}{Path(path).suffix}"

    def _resolve_upload_path(self, relative_path: str | None) -> Path | None:
        if not relative_path:
            return None
        path = Path(relative_path)
        if path.is_absolute():
            return path
        return settings.upload_folder / path

    def _write_json(self, path: Path, data: Any) -> None:
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def _iso(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.isoformat()
