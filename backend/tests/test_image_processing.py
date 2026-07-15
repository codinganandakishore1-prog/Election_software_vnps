"""Unit tests for candidate image processing utilities."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from app.exceptions.base import ValidationError
from app.utils import image_processing as ip


def _make_png_bytes(width: int, height: int, color: tuple[int, int, int] = (120, 80, 200)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buffer, format="PNG")
    return buffer.getvalue()


def test_validate_upload_accepts_valid_png() -> None:
    data = _make_png_bytes(400, 400)
    image = ip.validate_upload("candidate.png", "image/png", data)
    assert image.size == (400, 400)


def test_validate_upload_rejects_empty_file() -> None:
    with pytest.raises(ValidationError, match="empty"):
        ip.validate_upload("candidate.png", "image/png", b"")


def test_validate_upload_rejects_oversized_file() -> None:
    data = b"x" * (ip.MAX_UPLOAD_BYTES + 1)
    with pytest.raises(ValidationError, match="10 MB"):
        ip.validate_upload("candidate.png", "image/png", data)


def test_validate_upload_rejects_unsupported_extension() -> None:
    data = _make_png_bytes(400, 400)
    with pytest.raises(ValidationError, match="Unsupported image format"):
        ip.validate_upload("candidate.gif", "image/gif", data)


def test_validate_upload_rejects_small_resolution() -> None:
    data = _make_png_bytes(200, 200)
    with pytest.raises(ValidationError, match="at least 300"):
        ip.validate_upload("candidate.png", "image/png", data)


def test_crop_image_applies_selection() -> None:
    image = Image.new("RGBA", (400, 400), (255, 0, 0, 255))
    cropped = ip.crop_image(image, 50, 50, 100, 150)
    assert cropped.size == (100, 150)


def test_crop_image_rejects_out_of_bounds() -> None:
    image = Image.new("RGBA", (400, 400), (255, 0, 0, 255))
    with pytest.raises(ValidationError, match="within image bounds"):
        ip.crop_image(image, 350, 350, 100, 100)


def test_rotate_image_rotates_by_90_degrees() -> None:
    image = Image.new("RGBA", (400, 300), (0, 255, 0, 255))
    rotated = ip.rotate_image(image, 90)
    assert rotated.size == (300, 400)


def test_zoom_image_resizes_with_scale() -> None:
    image = Image.new("RGBA", (400, 400), (0, 0, 255, 255))
    zoomed = ip.zoom_image(image, 1.5)
    assert zoomed.size == (600, 600)


def test_zoom_image_rejects_invalid_scale() -> None:
    image = Image.new("RGBA", (400, 400), (0, 0, 255, 255))
    with pytest.raises(ValidationError, match="Zoom scale"):
        ip.zoom_image(image, 5.0)


def test_generate_thumbnail_fits_within_bounds() -> None:
    image = Image.new("RGBA", (800, 1000), (255, 255, 0, 255))
    thumbnail = ip.generate_thumbnail(image)
    assert thumbnail.width <= ip.THUMBNAIL_SIZE[0]
    assert thumbnail.height <= ip.THUMBNAIL_SIZE[1]


def test_generate_preview_fits_within_bounds() -> None:
    image = Image.new("RGBA", (1200, 1500), (255, 255, 0, 255))
    preview = ip.generate_preview(image)
    assert preview.width <= ip.PREVIEW_SIZE[0]
    assert preview.height <= ip.PREVIEW_SIZE[1]


def test_save_png_writes_file(tmp_path) -> None:
    image = Image.new("RGBA", (320, 320), (10, 20, 30, 255))
    target = tmp_path / "candidate.png"
    size = ip.save_png(image, target)
    assert target.exists()
    assert size > 0
