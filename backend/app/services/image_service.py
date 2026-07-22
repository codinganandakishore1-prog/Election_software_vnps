"""Image processing service."""

from __future__ import annotations

from pathlib import Path

from fastapi import UploadFile
from PIL import Image

from app.config.settings import settings
from app.database.seeds import new_uuid
from app.exceptions.base import NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.candidate import Candidate, CandidateImage
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.candidate_repository import CandidateImageRepository, CandidateRepository
from app.schemas.image import CropRequest, ImageResponse, ImageUploadResponse
from app.services.base import BaseService
from app.utils.image_processing import (
    crop_image,
    generate_large,
    generate_preview,
    generate_thumbnail,
    open_image,
    rotate_image,
    save_png,
    validate_upload,
    zoom_image,
)

IMAGE_SUBDIR = "candidate_images"
ORIGINAL_FILENAME = "original.png"
PROCESSED_FILENAME = "processed.png"
THUMBNAIL_FILENAME = "thumbnail.png"
PREVIEW_FILENAME = "preview.png"
LARGE_FILENAME = "large.png"


class ImageService(BaseService):
    """Handles candidate image upload and processing."""

    def __init__(
        self,
        candidate_repository: CandidateRepository,
        candidate_image_repository: CandidateImageRepository,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        self.candidate_repository = candidate_repository
        self.candidate_image_repository = candidate_image_repository
        self.audit_log_repository = audit_log_repository
        self.upload_root = settings.upload_folder / IMAGE_SUBDIR

    async def upload_for_candidate(
        self,
        candidate_id: str,
        file: UploadFile,
        *,
        user_id: str | None = None,
        replace: bool = False,
    ) -> ImageUploadResponse:
        """Upload or replace a candidate image."""
        candidate = self._get_candidate(candidate_id)
        data = await self._read_upload(file)
        image = validate_upload(file.filename, file.content_type, data)

        if replace and candidate.image_id:
            image_record = self._get_image(candidate.image_id)
            self._write_image_set(image_record.id, image)
            self._update_image_metadata(image_record, image, user_id=user_id)
            self._audit(user_id, f"Replaced image for candidate {candidate_id}", image_record.id)
        else:
            if candidate.image_id and not replace:
                raise ValidationError("Candidate already has an image. Use replace to upload a new one.")

            image_id = new_uuid()
            self._write_image_set(image_id, image)
            image_record = CandidateImage(
                id=image_id,
                original_path=self._relative_path(image_id, ORIGINAL_FILENAME),
                processed_path=self._relative_path(image_id, PROCESSED_FILENAME),
                thumbnail_path=self._relative_path(image_id, THUMBNAIL_FILENAME),
                width=image.width,
                height=image.height,
                file_size=self._absolute_path(image_id, PROCESSED_FILENAME).stat().st_size,
                mime_type="image/png",
                uploaded_by=user_id,
            )
            self.candidate_image_repository.add(image_record)
            candidate.image_id = image_id
            self._audit(user_id, f"Uploaded image for candidate {candidate_id}", image_id)

        self.candidate_image_repository.commit()
        return ImageUploadResponse(image_id=image_record.id, candidate_id=candidate.id)

    def get_metadata(self, image_id: str) -> ImageResponse:
        """Return image metadata."""
        image_record = self._get_image(image_id)
        return ImageResponse.model_validate(image_record)

    def resolve_image_path(self, image_id: str, variant: str) -> Path:
        """Resolve an on-disk image path for serving."""
        image_record = self._get_image(image_id)
        filename_map = {
            "original": ORIGINAL_FILENAME,
            "processed": PROCESSED_FILENAME,
            "thumbnail": THUMBNAIL_FILENAME,
            "preview": PREVIEW_FILENAME,
            "large": LARGE_FILENAME,
        }
        filename = filename_map.get(variant)
        if filename is None:
            raise ValidationError("Invalid image variant. Use original, processed, thumbnail, preview, or large")

        path = self._absolute_path(image_id, filename)
        if not path.exists():
            stored_path = getattr(image_record, f"{variant}_path", None)
            if stored_path:
                path = settings.upload_folder / stored_path
        if not path.exists():
            raise NotFoundError(f"{variant.title()} image not found")
        return path

    def crop(self, image_id: str, payload: CropRequest, *, user_id: str | None = None) -> ImageResponse:
        """Crop the working processed image."""
        image_record = self._get_image(image_id)
        processed = self._load_processed(image_id)
        cropped = crop_image(processed, payload.x, payload.y, payload.width, payload.height)
        self._save_processed_variants(image_id, cropped)
        self._update_image_metadata(image_record, cropped, user_id=user_id)
        self._audit(user_id, f"Cropped image {image_id}", image_id)
        self.candidate_image_repository.commit()
        return ImageResponse.model_validate(image_record)

    def rotate(self, image_id: str, angle: int, *, user_id: str | None = None) -> ImageResponse:
        """Rotate the working processed image."""
        image_record = self._get_image(image_id)
        processed = self._load_processed(image_id)
        rotated = rotate_image(processed, angle)
        self._save_processed_variants(image_id, rotated)
        self._update_image_metadata(image_record, rotated, user_id=user_id)
        self._audit(user_id, f"Rotated image {image_id} by {angle} degrees", image_id)
        self.candidate_image_repository.commit()
        return ImageResponse.model_validate(image_record)

    def zoom(self, image_id: str, scale: float, *, user_id: str | None = None) -> ImageResponse:
        """Zoom (resize) the working processed image."""
        image_record = self._get_image(image_id)
        processed = self._load_processed(image_id)
        zoomed = zoom_image(processed, scale)
        self._save_processed_variants(image_id, zoomed)
        self._update_image_metadata(image_record, zoomed, user_id=user_id)
        self._audit(user_id, f"Zoomed image {image_id} to scale {scale}", image_id)
        self.candidate_image_repository.commit()
        return ImageResponse.model_validate(image_record)

    def reset(self, image_id: str, *, user_id: str | None = None) -> ImageResponse:
        """Restore the processed image from the original upload."""
        image_record = self._get_image(image_id)
        original_path = self._absolute_path(image_id, ORIGINAL_FILENAME)
        if not original_path.exists():
            raise NotFoundError("Original image not found")

        original = open_image(original_path.read_bytes())
        self._save_processed_variants(image_id, original)
        self._update_image_metadata(image_record, original, user_id=user_id)
        self._audit(user_id, f"Reset image {image_id} to original", image_id)
        self.candidate_image_repository.commit()
        return ImageResponse.model_validate(image_record)

    def _get_candidate(self, candidate_id: str) -> Candidate:
        candidate = self.candidate_repository.get_by_id(candidate_id)
        if candidate is None:
            raise NotFoundError("Candidate not found")
        return candidate

    def _get_image(self, image_id: str) -> CandidateImage:
        image_record = self.candidate_image_repository.get_by_id(image_id)
        if image_record is None:
            raise NotFoundError("Image not found")
        return image_record

    async def _read_upload(self, file: UploadFile) -> bytes:
        data = await file.read()
        await file.seek(0)
        return data

    def _image_dir(self, image_id: str) -> Path:
        return self.upload_root / image_id

    def _relative_path(self, image_id: str, filename: str) -> str:
        return str(Path(IMAGE_SUBDIR) / image_id / filename)

    def _absolute_path(self, image_id: str, filename: str) -> Path:
        return self._image_dir(image_id) / filename

    def _write_image_set(self, image_id: str, image: Image.Image) -> None:
        """Persist original, processed, thumbnail, preview, and large variants."""
        image_dir = self._image_dir(image_id)
        image_dir.mkdir(parents=True, exist_ok=True)
        save_png(image, image_dir / ORIGINAL_FILENAME)
        self._save_processed_variants(image_id, image)

    def _save_processed_variants(self, image_id: str, image: Image.Image) -> None:
        image_dir = self._image_dir(image_id)
        image_dir.mkdir(parents=True, exist_ok=True)
        save_png(image, image_dir / PROCESSED_FILENAME)
        save_png(generate_thumbnail(image), image_dir / THUMBNAIL_FILENAME)
        save_png(generate_preview(image), image_dir / PREVIEW_FILENAME)
        save_png(generate_large(image), image_dir / LARGE_FILENAME)

    def _load_processed(self, image_id: str) -> Image.Image:
        path = self._absolute_path(image_id, PROCESSED_FILENAME)
        if not path.exists():
            raise NotFoundError("Processed image not found")
        return open_image(path.read_bytes())

    def _update_image_metadata(
        self,
        image_record: CandidateImage,
        image: Image.Image,
        *,
        user_id: str | None = None,
    ) -> None:
        processed_path = self._absolute_path(image_record.id, PROCESSED_FILENAME)
        image_record.width = image.width
        image_record.height = image.height
        image_record.file_size = processed_path.stat().st_size if processed_path.exists() else None
        image_record.mime_type = "image/png"
        image_record.processed_path = self._relative_path(image_record.id, PROCESSED_FILENAME)
        image_record.thumbnail_path = self._relative_path(image_record.id, THUMBNAIL_FILENAME)
        if user_id:
            image_record.uploaded_by = user_id

    def _audit(self, user_id: str | None, action: str, image_id: str) -> None:
        if not user_id:
            return
        self.audit_log_repository.add(
            AuditLog(
                id=new_uuid(),
                user_id=user_id,
                module="Candidate Images",
                action=action,
                new_value={"image_id": image_id},
            )
        )
