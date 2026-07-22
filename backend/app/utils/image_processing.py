"""Pillow-based candidate image processing utilities."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from app.exceptions.base import ValidationError

ALLOWED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".bmp"})
ALLOWED_MIME_TYPES = frozenset({"image/jpeg", "image/png", "image/webp", "image/bmp"})
PILLOW_FORMAT_TO_MIME = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
    "BMP": "image/bmp",
}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MIN_WIDTH = 300
MIN_HEIGHT = 300
THUMBNAIL_SIZE = (150, 180)
PREVIEW_SIZE = (400, 500)
LARGE_SIZE = (800, 1000)
ZOOM_MIN_SCALE = 0.25
ZOOM_MAX_SCALE = 4.0
RESAMPLING = Image.Resampling.LANCZOS


def _extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def _mime_from_image(image: Image.Image) -> str:
    pillow_format = (image.format or "PNG").upper()
    return PILLOW_FORMAT_TO_MIME.get(pillow_format, "image/png")


def open_image(data: bytes) -> Image.Image:
    """Open image bytes, apply EXIF orientation, and return an RGBA copy."""
    try:
        with Image.open(io.BytesIO(data)) as image:
            image = ImageOps.exif_transpose(image)
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA")
            return image.copy()
    except UnidentifiedImageError as exc:
        raise ValidationError("Corrupted or unsupported image file") from exc
    except OSError as exc:
        raise ValidationError("Corrupted or unsupported image file") from exc


def validate_upload(filename: str | None, content_type: str | None, data: bytes) -> Image.Image:
    """Validate an uploaded image and return a Pillow image."""
    if not data:
        raise ValidationError("Image file is empty")

    if len(data) > MAX_UPLOAD_BYTES:
        raise ValidationError("Image exceeds maximum upload size of 10 MB")

    extension = _extension(filename or "")
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError("Unsupported image format. Allowed: JPG, JPEG, PNG, WEBP, BMP")

    if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
        raise ValidationError("Unsupported image MIME type")

    image = open_image(data)
    mime_type = _mime_from_image(image)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValidationError("Unsupported image format")

    width, height = image.size
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        raise ValidationError(f"Image must be at least {MIN_WIDTH} x {MIN_HEIGHT} pixels")

    return image


def save_png(image: Image.Image, path: Path) -> int:
    """Save an image as PNG and return file size in bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)
    return path.stat().st_size


def crop_image(image: Image.Image, x: int, y: int, width: int, height: int) -> Image.Image:
    """Crop an image using pixel coordinates."""
    if width <= 0 or height <= 0:
        raise ValidationError("Crop width and height must be positive")

    img_width, img_height = image.size
    if x < 0 or y < 0 or x + width > img_width or y + height > img_height:
        raise ValidationError("Crop area must be within image bounds")

    if width < 5 or height < 5:
        raise ValidationError("Crop area is too small")

    return image.crop((x, y, x + width, y + height))


def rotate_image(image: Image.Image, angle: int) -> Image.Image:
    """Rotate an image by the given angle in degrees."""
    if angle not in (-360, -270, -180, -90, 0, 90, 180, 270, 360):
        raise ValidationError("Rotation angle must be a multiple of 90 degrees")
    if angle in (0, 360, -360):
        return image.copy()
    return image.rotate(angle, expand=True, resample=RESAMPLING)


def zoom_image(image: Image.Image, scale: float) -> Image.Image:
    """Resize an image by scale factor, clamped to 25%–400%."""
    if scale < ZOOM_MIN_SCALE or scale > ZOOM_MAX_SCALE:
        raise ValidationError(f"Zoom scale must be between {ZOOM_MIN_SCALE} and {ZOOM_MAX_SCALE}")

    width, height = image.size
    new_width = max(1, int(width * scale))
    new_height = max(1, int(height * scale))
    return image.resize((new_width, new_height), RESAMPLING)


def fit_within(image: Image.Image, max_size: tuple[int, int]) -> Image.Image:
    """Resize an image to fit within max_size while preserving aspect ratio."""
    max_width, max_height = max_size
    width, height = image.size
    ratio = min(max_width / width, max_height / height, 1.0)
    if ratio >= 1.0:
        return image.copy()
    new_width = max(1, int(width * ratio))
    new_height = max(1, int(height * ratio))
    return image.resize((new_width, new_height), RESAMPLING)


def generate_thumbnail(image: Image.Image) -> Image.Image:
    """Generate a thumbnail that fits within THUMBNAIL_SIZE."""
    return fit_within(image, THUMBNAIL_SIZE)


def generate_preview(image: Image.Image) -> Image.Image:
    """Generate a voting-card preview that fits within PREVIEW_SIZE."""
    return fit_within(image, PREVIEW_SIZE)


def generate_large(image: Image.Image) -> Image.Image:
    """Generate a large display version that fits within LARGE_SIZE."""
    return fit_within(image, LARGE_SIZE)
