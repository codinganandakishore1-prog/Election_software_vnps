"""Local candidate photo editing helpers (mirrors desktop ImageEditor)."""

from __future__ import annotations

import base64
import io

from PIL import Image, ImageOps

ZOOM_STEP = 1.25
ZOOM_MIN = 0.25
ZOOM_MAX = 4.0
RESAMPLING = Image.Resampling.LANCZOS


def open_image_bytes(data: bytes) -> Image.Image:
    """Open image bytes with EXIF orientation applied."""
    with Image.open(io.BytesIO(data)) as image:
        image = ImageOps.exif_transpose(image)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA")
        return image.copy()


def image_to_png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    to_save = image.convert("RGBA") if image.mode not in ("RGB", "RGBA") else image
    to_save.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def image_to_data_url(image: Image.Image, *, mime: str = "image/png") -> str:
    encoded = base64.b64encode(image_to_png_bytes(image)).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def bytes_to_data_url(data: bytes, *, content_type: str = "image/png") -> str:
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def rotate_image(image: Image.Image, angle: int) -> Image.Image:
    return image.rotate(angle, expand=True, resample=RESAMPLING)


def zoom_image(image: Image.Image, factor: float) -> Image.Image:
    """Resize by a relative factor, clamped so neither side collapses or explodes."""
    clamped = max(ZOOM_MIN, min(ZOOM_MAX, factor))
    width, height = image.size
    new_width = max(1, int(width * clamped))
    new_height = max(1, int(height * clamped))
    return image.resize((new_width, new_height), RESAMPLING)


def portrait_crop(width: int, height: int) -> tuple[int, int, int, int]:
    target_ratio = 3 / 4
    if width / height > target_ratio:
        crop_h = height
        crop_w = max(5, int(height * target_ratio))
    else:
        crop_w = width
        crop_h = max(5, int(width / target_ratio))
    x = max(0, (width - crop_w) // 2)
    y = max(0, (height - crop_h) // 2)
    return x, y, crop_w, crop_h


def square_crop(width: int, height: int) -> tuple[int, int, int, int]:
    side = min(width, height)
    x = max(0, (width - side) // 2)
    y = max(0, (height - side) // 2)
    return x, y, side, side


def landscape_crop(width: int, height: int) -> tuple[int, int, int, int]:
    target_ratio = 4 / 3
    if width / height > target_ratio:
        crop_h = height
        crop_w = max(5, int(height * target_ratio))
    else:
        crop_w = width
        crop_h = max(5, int(width / target_ratio))
    x = max(0, (width - crop_w) // 2)
    y = max(0, (height - crop_h) // 2)
    return x, y, crop_w, crop_h


def apply_crop_mode(image: Image.Image, mode: str) -> Image.Image:
    width, height = image.size
    if mode == "square":
        x, y, crop_w, crop_h = square_crop(width, height)
    elif mode == "landscape":
        x, y, crop_w, crop_h = landscape_crop(width, height)
    else:
        x, y, crop_w, crop_h = portrait_crop(width, height)
    return image.crop((x, y, x + crop_w, y + crop_h))
