"""Configuration package generation tests."""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from election_platform.enums.election import CandidateStatus, ElectionStatus, ElectionType
from election_platform.utils.checksum import CHECKSUM_FILENAME, compute_directory_checksum
from PIL import Image

from app.models.candidate import Candidate, CandidateImage
from app.models.election import Election
from app.models.house import House
from app.models.position import Position
from app.models.settings import SystemSettings, Theme
from app.services.config_package_service import (
    IMAGES_DIR,
    LOGO_DIR,
    PACKAGE_JSON_FILES,
    ConfigPackageService,
)


def _png_bytes(width: int = 200, height: int = 200) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGBA", (width, height), (241, 125, 50, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


def _write_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_png_bytes())


@pytest.fixture
def package_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    upload_folder = tmp_path / "uploads"
    package_folder = tmp_path / "packages"
    upload_folder.mkdir()
    package_folder.mkdir()

    from app.config import settings

    monkeypatch.setattr(settings, "upload_folder", upload_folder)
    monkeypatch.setattr(settings, "config_package_folder", package_folder)
    return upload_folder, package_folder


def _make_service(
    *,
    election: Election,
    positions: list[Position],
    candidates: list[Candidate],
    houses: list[House],
    images: dict[str, CandidateImage],
    settings_obj: SystemSettings | None,
    theme: Theme | None,
) -> ConfigPackageService:
    election_repo = MagicMock()
    position_repo = MagicMock()
    position_repo.list_for_election.return_value = positions
    candidate_repo = MagicMock()
    candidate_repo.list_for_election.return_value = candidates
    image_repo = MagicMock()
    image_repo.get_by_id.side_effect = lambda image_id: images.get(image_id)
    house_repo = MagicMock()
    house_repo.list_all_ordered.return_value = houses
    settings_repo = MagicMock()
    settings_repo.get_active.return_value = settings_obj
    theme_repo = MagicMock()
    theme_repo.get_active.return_value = theme

    return ConfigPackageService(
        election_repo,
        position_repo,
        candidate_repo,
        image_repo,
        house_repo,
        settings_repo,
        theme_repo,
    )


def _build_fixture_data(upload_folder: Path) -> dict:
    now = datetime.now(timezone.utc)
    election_id = "election-test-001"
    position_id = "position-test-001"
    candidate_id = "candidate-test-001"
    house_id = "house-test-001"
    image_id = "image-test-001"
    theme_id = "theme-test-001"

    election_logo = upload_folder / "elections" / "election_logo.png"
    _write_png(election_logo)
    candidate_processed = upload_folder / "candidates" / f"{candidate_id}.png"
    candidate_thumb = upload_folder / "candidates" / f"{candidate_id}_thumb.png"
    candidate_original = upload_folder / "candidates" / f"{candidate_id}_original.png"
    _write_png(candidate_processed)
    _write_png(candidate_thumb)
    _write_png(candidate_original)
    house_logo = upload_folder / "houses" / "pallava.png"
    _write_png(house_logo)
    school_logo = upload_folder / "themes" / theme_id / "school_logo.png"
    election_theme_logo = upload_folder / "themes" / theme_id / "election_logo.png"
    background_light = upload_folder / "themes" / theme_id / "background_light.png"
    app_icon = upload_folder / "themes" / theme_id / "app_icon.png"
    for asset in (school_logo, election_theme_logo, background_light, app_icon):
        _write_png(asset)

    election = Election(
        id=election_id,
        election_name="Annual Student Council Election",
        academic_year="2026-2027",
        description="School-wide election",
        version=0,
        status=ElectionStatus.DRAFT,
        logo_path=str(election_logo.relative_to(upload_folder)),
        configuration_locked=False,
        created_at=now,
        updated_at=now,
    )
    position = Position(
        id=position_id,
        election_id=election_id,
        election_type=ElectionType.REGULAR,
        position_name="Head Boy",
        winner_count=1,
        display_order=1,
        created_at=now,
        updated_at=now,
    )
    house = House(
        id=house_id,
        house_name="Pallava",
        color="#F17D32",
        logo_path=str(house_logo.relative_to(upload_folder)),
        active=True,
    )
    image = CandidateImage(
        id=image_id,
        original_path=str(candidate_original.relative_to(upload_folder)),
        processed_path=str(candidate_processed.relative_to(upload_folder)),
        thumbnail_path=str(candidate_thumb.relative_to(upload_folder)),
        width=200,
        height=200,
        mime_type="image/png",
    )
    candidate = Candidate(
        id=candidate_id,
        election_id=election_id,
        position_id=position_id,
        house_id=None,
        candidate_name="Alice Johnson",
        display_order=1,
        image_id=image_id,
        status=CandidateStatus.DRAFT,
        created_at=now,
        updated_at=now,
    )
    system_settings = SystemSettings(
        id="settings-test-001",
        school_name="VNPS",
        school_logo="school_logo.png",
        election_logo="election_logo.png",
        primary_color="#F17D32",
        secondary_color="#1A1A2E",
        timezone="Asia/Kolkata",
        maintenance_mode=False,
        created_at=now,
        updated_at=now,
    )
    theme = Theme(
        id=theme_id,
        theme_name="VNPS Default",
        school_name="VNPS",
        font_heading="Oswald",
        font_body="Inter",
        font_accent="Playfair Display",
        primary_color="#F17D32",
        school_logo_path=str(school_logo.relative_to(upload_folder)),
        election_logo_path=str(election_theme_logo.relative_to(upload_folder)),
        background_light_path=str(background_light.relative_to(upload_folder)),
        icon_app_path=str(app_icon.relative_to(upload_folder)),
        active=True,
        created_at=now,
        updated_at=now,
    )

    return {
        "election": election,
        "positions": [position],
        "candidates": [candidate],
        "houses": [house],
        "images": {image_id: image},
        "settings": system_settings,
        "theme": theme,
    }


def test_build_package_matches_srs_structure(package_paths: tuple[Path, Path]) -> None:
    upload_folder, _package_folder = package_paths
    data = _build_fixture_data(upload_folder)
    service = _make_service(
        election=data["election"],
        positions=data["positions"],
        candidates=data["candidates"],
        houses=data["houses"],
        images=data["images"],
        settings_obj=data["settings"],
        theme=data["theme"],
    )

    result = service.build_package(data["election"], version=1)

    assert Path(result.package_path).exists()
    assert result.package_size > 0
    assert len(result.checksum) == 64

    with zipfile.ZipFile(result.package_path, "r") as archive:
        names = set(archive.namelist())

        for json_file in PACKAGE_JSON_FILES:
            assert json_file in names, f"Missing required JSON file: {json_file}"

        assert f"{IMAGES_DIR}/" in " ".join(names)
        assert f"{LOGO_DIR}/" in " ".join(names)
        assert CHECKSUM_FILENAME in names
        assert "Nodes.json" not in names

        election_payload = json.loads(archive.read("Election.json"))
        assert election_payload["version"] == 1
        assert election_payload["checksum_algorithm"] == "SHA-256"
        assert election_payload["name"] == "Annual Student Council Election"

        candidates_payload = json.loads(archive.read("Candidates.json"))
        assert len(candidates_payload) == 1
        assert candidates_payload[0]["image_file"] == f"{data['candidates'][0].id}.png"
        assert candidates_payload[0]["image_thumbnail"] == f"{data['candidates'][0].id}_thumb.png"
        assert candidates_payload[0]["image_original"] == f"{data['candidates'][0].id}_original.png"

        theme_payload = json.loads(archive.read("Theme.json"))
        assert theme_payload["assets"]["school_logo"] == f"{LOGO_DIR}/school_logo.png"
        assert theme_payload["assets"]["background_light"] == f"{IMAGES_DIR}/background_light.png"

        checksum_in_zip = archive.read(CHECKSUM_FILENAME).decode("utf-8").strip()
        assert checksum_in_zip == result.checksum


def test_build_package_checksum_matches_directory_digest(package_paths: tuple[Path, Path]) -> None:
    upload_folder, _ = package_paths
    data = _build_fixture_data(upload_folder)
    service = _make_service(
        election=data["election"],
        positions=data["positions"],
        candidates=data["candidates"],
        houses=data["houses"],
        images=data["images"],
        settings_obj=data["settings"],
        theme=data["theme"],
    )

    result = service.build_package(data["election"], version=2)

    with zipfile.ZipFile(result.package_path, "r") as archive:
        extract_dir = Path(result.package_path).parent / "verify_extract"
        extract_dir.mkdir(exist_ok=True)
        archive.extractall(extract_dir)

        recomputed = compute_directory_checksum(extract_dir)
        assert recomputed == result.checksum


def test_build_package_includes_candidate_and_logo_assets(package_paths: tuple[Path, Path]) -> None:
    upload_folder, _ = package_paths
    data = _build_fixture_data(upload_folder)
    service = _make_service(
        election=data["election"],
        positions=data["positions"],
        candidates=data["candidates"],
        houses=data["houses"],
        images=data["images"],
        settings_obj=data["settings"],
        theme=data["theme"],
    )

    result = service.build_package(data["election"], version=3)

    with zipfile.ZipFile(result.package_path, "r") as archive:
        names = archive.namelist()
        candidate_id = data["candidates"][0].id
        house_id = data["houses"][0].id
        election_id = data["election"].id

        assert f"{IMAGES_DIR}/{candidate_id}.png" in names
        assert f"{IMAGES_DIR}/{candidate_id}_thumb.png" in names
        assert f"{IMAGES_DIR}/{candidate_id}_original.png" in names
        assert f"{LOGO_DIR}/house_{house_id}.png" in names
        assert f"{LOGO_DIR}/election_{election_id}.png" in names
        assert f"{LOGO_DIR}/school_logo.png" in names
        assert f"{IMAGES_DIR}/background_light.png" in names
