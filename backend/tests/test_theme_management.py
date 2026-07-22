"""Theme and branding management tests."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from app.services.theme_service import ASSET_TYPES, ThemeService


def _png_bytes(width: int = 400, height: int = 400) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGBA", (width, height), (241, 125, 50, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


class FakeUploadFile:
    def __init__(self, data: bytes, filename: str = "logo.png", content_type: str = "image/png") -> None:
        self._data = data
        self.filename = filename
        self.content_type = content_type

    async def read(self) -> bytes:
        return self._data


def test_asset_types_cover_branding_requirements() -> None:
    assert "school_logo" in ASSET_TYPES
    assert "election_logo" in ASSET_TYPES
    assert "background_light" in ASSET_TYPES
    assert "background_dark" in ASSET_TYPES
    assert "background_welcome" in ASSET_TYPES
    assert "icon_app" in ASSET_TYPES
    assert "icon_favicon" in ASSET_TYPES


def test_default_theme_assets_exist() -> None:
    assets_dir = Path(__file__).resolve().parents[1] / "app" / "assets" / "default_theme"
    for filename in (
        "school_logo.png",
        "election_logo.png",
        "background_light.png",
        "background_dark.png",
        "background_welcome.png",
        "app_icon.png",
        "favicon.png",
    ):
        assert (assets_dir / filename).exists(), f"Missing default asset: {filename}"


def test_serialize_theme_structure() -> None:
    from app.models.settings import Theme

    theme = Theme(
        id="test-theme",
        theme_name="Test",
        school_name="VNPS",
        font_heading="Oswald",
        font_body="Inter",
        font_accent="Playfair Display",
        primary_color="#F17D32",
        school_logo_path="themes/test/school_logo.png",
        active=True,
    )
    service = ThemeService.__new__(ThemeService)
    payload = service.serialize_theme(theme)
    assert payload["theme_name"] == "Test"
    assert payload["school_name"] == "VNPS"
    assert payload["fonts"]["heading"] == "Oswald"
    assert payload["colors"]["primary"] == "#F17D32"
    assert payload["assets"]["school_logo"] == "school_logo.png"
