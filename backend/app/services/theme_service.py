"""Theme and branding management service."""

from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from PIL import Image

from election_platform.utils.checksum import CHECKSUM_FILENAME, compute_directory_checksum

from app.config.settings import settings
from app.database.seeds import new_uuid
from app.exceptions.base import NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.settings import Theme
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.settings_repository import ThemeRepository
from app.schemas.theme import (
    ThemeAssetUploadResponse,
    ThemeCreate,
    ThemeDownloadResponse,
    ThemeResponse,
    ThemeUpdate,
)
from app.services.base import BaseService
from app.utils.image_processing import open_image, validate_upload

THEME_SUBDIR = "themes"
PACKAGE_SUBDIR = "theme_packages"

ASSET_TYPES = frozenset(
    {
        "school_logo",
        "election_logo",
        "background_light",
        "background_dark",
        "background_welcome",
        "icon_app",
        "icon_favicon",
    }
)

ASSET_FIELD_MAP = {
    "school_logo": "school_logo_path",
    "election_logo": "election_logo_path",
    "background_light": "background_light_path",
    "background_dark": "background_dark_path",
    "background_welcome": "background_welcome_path",
    "icon_app": "icon_app_path",
    "icon_favicon": "icon_favicon_path",
}

ASSET_FILENAME_MAP = {
    "school_logo": "school_logo.png",
    "election_logo": "election_logo.png",
    "background_light": "background_light.png",
    "background_dark": "background_dark.png",
    "background_welcome": "background_welcome.png",
    "icon_app": "app_icon.png",
    "icon_favicon": "favicon.png",
}

DEFAULT_THEME_ID = "00000000-0000-4000-8000-000000000201"


@dataclass
class ThemePackageResult:
    """Built theme asset package."""

    package_path: Path
    checksum: str
    package_size: int


class ThemeService(BaseService):
    """Handles theme CRUD, asset uploads, and downloadable packages."""

    def __init__(
        self,
        theme_repository: ThemeRepository,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        self.theme_repository = theme_repository
        self.audit_log_repository = audit_log_repository
        self.upload_root = settings.upload_folder / THEME_SUBDIR
        self.package_root = settings.upload_folder / PACKAGE_SUBDIR

    def list_themes(self) -> list[ThemeResponse]:
        """Return all active (non-deleted) themes."""
        themes = self.theme_repository.list_all_ordered()
        return [self._to_response(theme) for theme in themes]

    def get_theme(self, theme_id: str) -> ThemeResponse:
        """Return a single theme."""
        return self._to_response(self._get_theme(theme_id))

    def get_active_theme(self) -> ThemeResponse | None:
        """Return the currently active theme."""
        theme = self.theme_repository.get_active()
        if theme is None:
            return None
        return self._to_response(theme)

    def create_theme(self, payload: ThemeCreate, *, user_id: str | None = None) -> ThemeResponse:
        """Create a new theme record."""
        theme = Theme(
            id=new_uuid(),
            theme_name=payload.theme_name.strip(),
            school_name=payload.school_name,
            font_heading=payload.font_heading,
            font_body=payload.font_body,
            font_accent=payload.font_accent,
            primary_color=payload.primary_color,
            secondary_color=payload.secondary_color,
            accent_color=payload.accent_color,
            warning_color=payload.warning_color,
            danger_color=payload.danger_color,
            background_color=payload.background_color,
            surface_color=payload.surface_color,
            text_primary_color=payload.text_primary_color,
            text_secondary_color=payload.text_secondary_color,
            active=False,
        )
        self.theme_repository.add(theme)
        self._audit(user_id, "Theme Created", {"theme_id": theme.id, "theme_name": theme.theme_name})
        self.theme_repository.commit()
        return self._to_response(theme)

    def update_theme(
        self,
        theme_id: str,
        payload: ThemeUpdate,
        *,
        user_id: str | None = None,
    ) -> ThemeResponse:
        """Update theme metadata and colors."""
        theme = self._get_theme(theme_id)
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            if field == "theme_name" and value is not None:
                value = value.strip()
            setattr(theme, field, value)
        self._audit(user_id, "Theme Updated", {"theme_id": theme.id, "changes": updates})
        self.theme_repository.commit()
        return self._to_response(theme)

    def delete_theme(self, theme_id: str, *, user_id: str | None = None) -> None:
        """Soft-delete a theme. Active themes cannot be deleted."""
        theme = self._get_theme(theme_id)
        if theme.active:
            raise ValidationError("Cannot delete the active theme. Activate another theme first.")
        self.theme_repository.soft_delete(theme)
        self._audit(user_id, "Theme Deleted", {"theme_id": theme.id})
        self.theme_repository.commit()

    def activate_theme(self, theme_id: str, *, user_id: str | None = None) -> ThemeResponse:
        """Set a theme as the active branding theme."""
        theme = self._get_theme(theme_id)
        for existing in self.theme_repository.list_active():
            if existing.id != theme.id:
                existing.active = False
        theme.active = True
        self._audit(user_id, "Theme Activated", {"theme_id": theme.id, "theme_name": theme.theme_name})
        self.theme_repository.commit()
        return self._to_response(theme)

    async def upload_asset(
        self,
        theme_id: str,
        asset_type: str,
        file: UploadFile,
        *,
        user_id: str | None = None,
    ) -> ThemeAssetUploadResponse:
        """Upload or replace a theme asset image."""
        if asset_type not in ASSET_TYPES:
            raise ValidationError(f"Invalid asset type. Use one of: {', '.join(sorted(ASSET_TYPES))}")

        theme = self._get_theme(theme_id)
        data = await file.read()
        image = self._validate_theme_upload(file.filename, file.content_type, data, asset_type)

        if asset_type in {"icon_app", "icon_favicon"}:
            image = self._resize_icon(image)

        filename = ASSET_FILENAME_MAP[asset_type]
        relative_path = self._save_asset(theme.id, filename, image)
        field_name = ASSET_FIELD_MAP[asset_type]
        setattr(theme, field_name, relative_path)

        if asset_type == "election_logo":
            theme.logo_path = relative_path

        self._audit(
            user_id,
            f"Theme Asset Uploaded ({asset_type})",
            {"theme_id": theme.id, "asset_type": asset_type, "path": relative_path},
        )
        self.theme_repository.commit()
        return ThemeAssetUploadResponse(theme_id=theme.id, asset_type=asset_type, path=relative_path)

    def resolve_asset_path(self, theme_id: str, asset_type: str) -> Path:
        """Resolve an on-disk asset path for serving."""
        if asset_type not in ASSET_TYPES:
            raise ValidationError(f"Invalid asset type. Use one of: {', '.join(sorted(ASSET_TYPES))}")

        theme = self._get_theme(theme_id)
        field_name = ASSET_FIELD_MAP[asset_type]
        relative_path = getattr(theme, field_name)
        if not relative_path:
            raise NotFoundError(f"{asset_type.replace('_', ' ').title()} not configured for this theme")

        path = self._resolve_upload_path(relative_path)
        if path is None or not path.exists():
            raise NotFoundError("Theme asset file not found on disk")
        return path

    def build_download_package(self, theme_id: str) -> ThemePackageResult:
        """Build a ZIP package of all theme assets and metadata."""
        theme = self._get_theme(theme_id)
        package_dir = self.package_root / theme.id
        package_dir.mkdir(parents=True, exist_ok=True)

        staging_dir = package_dir / "staging"
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        staging_dir.mkdir(parents=True)

        logos_dir = staging_dir / "Logos"
        backgrounds_dir = staging_dir / "Backgrounds"
        icons_dir = staging_dir / "Icons"
        logos_dir.mkdir()
        backgrounds_dir.mkdir()
        icons_dir.mkdir()

        theme_json = self.serialize_theme(theme)
        (staging_dir / "Theme.json").write_text(
            json.dumps(theme_json, indent=2, default=str),
            encoding="utf-8",
        )

        self._copy_asset_to_dir(theme.school_logo_path, logos_dir, "school_logo.png")
        self._copy_asset_to_dir(theme.election_logo_path, logos_dir, "election_logo.png")
        self._copy_asset_to_dir(theme.background_light_path, backgrounds_dir, "background_light.png")
        self._copy_asset_to_dir(theme.background_dark_path, backgrounds_dir, "background_dark.png")
        self._copy_asset_to_dir(theme.background_welcome_path, backgrounds_dir, "background_welcome.png")
        self._copy_asset_to_dir(theme.icon_app_path, icons_dir, "app_icon.png")
        self._copy_asset_to_dir(theme.icon_favicon_path, icons_dir, "favicon.png")

        checksum = compute_directory_checksum(staging_dir)
        (staging_dir / CHECKSUM_FILENAME).write_text(checksum, encoding="utf-8")

        safe_name = theme.theme_name.lower().replace(" ", "_")
        zip_path = package_dir / f"{safe_name}_theme_assets.zip"
        if zip_path.exists():
            zip_path.unlink()

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path in sorted(staging_dir.rglob("*")):
                if file_path.is_file():
                    archive.write(file_path, arcname=file_path.relative_to(staging_dir).as_posix())

        shutil.rmtree(staging_dir)

        return ThemePackageResult(
            package_path=zip_path,
            checksum=checksum,
            package_size=zip_path.stat().st_size,
        )

    def get_download_response(self, theme_id: str, api_prefix: str) -> ThemeDownloadResponse:
        """Build theme package and return download metadata."""
        result = self.build_download_package(theme_id)
        theme = self._get_theme(theme_id)
        return ThemeDownloadResponse(
            theme_id=theme.id,
            filename=result.package_path.name,
            download_url=f"{api_prefix}/themes/{theme.id}/download/file",
            checksum=result.checksum,
            package_size=result.package_size,
        )

    def resolve_package_path(self, theme_id: str) -> Path:
        """Return the most recently built package path for a theme."""
        theme = self._get_theme(theme_id)
        package_dir = self.package_root / theme.id
        if not package_dir.exists():
            result = self.build_download_package(theme_id)
            return result.package_path

        packages = sorted(package_dir.glob("*_theme_assets.zip"), key=lambda path: path.stat().st_mtime)
        if not packages:
            result = self.build_download_package(theme_id)
            return result.package_path
        return packages[-1]

    def serialize_theme(self, theme: Theme) -> dict[str, Any]:
        """Serialize theme for Theme.json in configuration packages."""
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
                "school_logo": self._asset_filename(theme.school_logo_path, "school_logo.png"),
                "election_logo": self._asset_filename(theme.election_logo_path, "election_logo.png"),
                "background_light": self._asset_filename(theme.background_light_path, "background_light.png"),
                "background_dark": self._asset_filename(theme.background_dark_path, "background_dark.png"),
                "background_welcome": self._asset_filename(
                    theme.background_welcome_path,
                    "background_welcome.png",
                ),
                "icon_app": self._asset_filename(theme.icon_app_path, "app_icon.png"),
                "icon_favicon": self._asset_filename(theme.icon_favicon_path, "favicon.png"),
            },
        }

    def seed_default_theme(self) -> bool:
        """Create the default VNPS branding theme if missing. Returns True if created."""
        existing = self.theme_repository.get_by_id(DEFAULT_THEME_ID)
        if existing is not None:
            return False

        theme = Theme(
            id=DEFAULT_THEME_ID,
            theme_name="VNPS Default",
            school_name="Vidhya Niketan Public School",
            font_heading="Oswald",
            font_body="Inter",
            font_accent="Playfair Display",
            primary_color="#F17D32",
            secondary_color="#1E3A5F",
            accent_color="#16A34A",
            warning_color="#EA580C",
            danger_color="#DC2626",
            background_color="#F3F4F6",
            surface_color="#FFFFFF",
            text_primary_color="#111827",
            text_secondary_color="#6B7280",
            active=True,
        )
        self.theme_repository.add(theme)
        self.theme_repository.flush()

        assets_dir = Path(__file__).resolve().parents[1] / "assets" / "default_theme"
        asset_mapping = {
            "school_logo.png": "school_logo_path",
            "election_logo.png": "election_logo_path",
            "background_light.png": "background_light_path",
            "background_dark.png": "background_dark_path",
            "background_welcome.png": "background_welcome_path",
            "app_icon.png": "icon_app_path",
            "favicon.png": "icon_favicon_path",
        }

        for filename, field_name in asset_mapping.items():
            source = assets_dir / filename
            if not source.exists():
                continue
            relative_path = self._copy_seed_asset(theme.id, filename, source)
            setattr(theme, field_name, relative_path)
            if field_name == "election_logo_path":
                theme.logo_path = relative_path

        self.theme_repository.commit()
        return True

    def _get_theme(self, theme_id: str) -> Theme:
        theme = self.theme_repository.get_by_id(theme_id)
        if theme is None:
            raise NotFoundError("Theme not found")
        return theme

    def _to_response(self, theme: Theme) -> ThemeResponse:
        return ThemeResponse.model_validate(theme)

    def _save_asset(self, theme_id: str, filename: str, image: Image.Image) -> str:
        theme_dir = self.upload_root / theme_id
        theme_dir.mkdir(parents=True, exist_ok=True)
        destination = theme_dir / filename
        image.save(destination, format="PNG", optimize=True)
        return str(Path(THEME_SUBDIR) / theme_id / filename)

    def _copy_seed_asset(self, theme_id: str, filename: str, source: Path) -> str:
        theme_dir = self.upload_root / theme_id
        theme_dir.mkdir(parents=True, exist_ok=True)
        destination = theme_dir / filename
        shutil.copy2(source, destination)
        return str(Path(THEME_SUBDIR) / theme_id / filename)

    def _copy_asset_to_dir(self, relative_path: str | None, target_dir: Path, filename: str) -> None:
        if not relative_path:
            return
        source = self._resolve_upload_path(relative_path)
        if source is None or not source.exists():
            return
        shutil.copy2(source, target_dir / filename)

    def _resolve_upload_path(self, relative_path: str | None) -> Path | None:
        if not relative_path:
            return None
        path = Path(relative_path)
        if path.is_absolute():
            return path
        return settings.upload_folder / path

    def _asset_filename(self, relative_path: str | None, default: str) -> str | None:
        if not relative_path:
            return None
        return default

    def _validate_theme_upload(
        self,
        filename: str | None,
        content_type: str | None,
        data: bytes,
        asset_type: str,
    ) -> Image.Image:
        """Validate theme asset uploads with relaxed size rules for icons."""
        if asset_type in {"icon_app", "icon_favicon"}:
            from app.utils.image_processing import ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES, MAX_UPLOAD_BYTES, open_image

            if not data:
                raise ValidationError("Image file is empty")
            if len(data) > MAX_UPLOAD_BYTES:
                raise ValidationError("Image file exceeds maximum size of 10 MB")
            ext = Path(filename or "").suffix.lower()
            if ext and ext not in ALLOWED_EXTENSIONS:
                raise ValidationError("Unsupported image format. Use JPG, PNG, or WebP")
            if content_type and content_type not in ALLOWED_MIME_TYPES:
                raise ValidationError("Unsupported image MIME type")
            return open_image(data)
        return validate_upload(filename, content_type, data)

    def _resize_icon(self, image: Image.Image, size: int = 512) -> Image.Image:
        """Resize icon uploads to a square PNG."""
        image = image.convert("RGBA")
        image.thumbnail((size, size), Image.Resampling.LANCZOS)
        square = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        offset = ((size - image.width) // 2, (size - image.height) // 2)
        square.paste(image, offset, image if image.mode == "RGBA" else None)
        return square

    def _audit(self, user_id: str | None, action: str, details: dict[str, Any]) -> None:
        if not user_id:
            return
        self.audit_log_repository.add(
            AuditLog(
                id=new_uuid(),
                user_id=user_id,
                module="Theme",
                action=action,
                new_value=details,
            )
        )
