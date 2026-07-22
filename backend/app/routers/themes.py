"""Theme and branding management router."""

from election_platform.enums.roles import UserRole
from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse

from app.config.settings import settings
from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.providers import ServiceContainer
from app.schemas.theme import (
    ThemeAssetUploadResponse,
    ThemeCreate,
    ThemeDownloadResponse,
    ThemeResponse,
    ThemeUpdate,
)

router = APIRouter()

AdminUser = Depends(require_roles(UserRole.SUPER_ADMINISTRATOR, UserRole.ADMINISTRATOR))


@router.get("")
async def list_themes(
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[list[ThemeResponse]]:
    """List all branding themes."""
    _ = current_user
    themes = container.theme_service.list_themes()
    return APIResponse.ok(data=themes)


@router.get("/active")
async def get_active_theme(
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[ThemeResponse | None]:
    """Return the currently active theme."""
    _ = current_user
    theme = container.theme_service.get_active_theme()
    return APIResponse.ok(data=theme)


@router.get("/{theme_id}")
async def get_theme(
    theme_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[ThemeResponse]:
    """Return a single theme."""
    _ = current_user
    theme = container.theme_service.get_theme(theme_id)
    return APIResponse.ok(data=theme)


@router.post("")
async def create_theme(
    payload: ThemeCreate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[ThemeResponse]:
    """Create a new branding theme."""
    theme = container.theme_service.create_theme(payload, user_id=current_user.id)
    return APIResponse.ok(message="Theme created successfully", data=theme)


@router.put("/{theme_id}")
async def update_theme(
    theme_id: str,
    payload: ThemeUpdate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[ThemeResponse]:
    """Update theme metadata and colors."""
    theme = container.theme_service.update_theme(theme_id, payload, user_id=current_user.id)
    return APIResponse.ok(message="Theme updated successfully", data=theme)


@router.delete("/{theme_id}")
async def delete_theme(
    theme_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[None]:
    """Soft-delete a theme."""
    container.theme_service.delete_theme(theme_id, user_id=current_user.id)
    return APIResponse.ok(message="Theme deleted successfully")


@router.post("/{theme_id}/activate")
async def activate_theme(
    theme_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[ThemeResponse]:
    """Set a theme as the active branding theme."""
    theme = container.theme_service.activate_theme(theme_id, user_id=current_user.id)
    return APIResponse.ok(message="Theme activated successfully", data=theme)


@router.post("/{theme_id}/assets/{asset_type}")
async def upload_theme_asset(
    theme_id: str,
    asset_type: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    file: UploadFile = File(...),
    _: None = AdminUser,
) -> APIResponse[ThemeAssetUploadResponse]:
    """Upload or replace a theme asset (logo, background, icon)."""
    result = await container.theme_service.upload_asset(
        theme_id,
        asset_type,
        file,
        user_id=current_user.id,
    )
    return APIResponse.ok(message="Theme asset uploaded successfully", data=result)


@router.get("/{theme_id}/assets/{asset_type}")
async def get_theme_asset(
    theme_id: str,
    asset_type: str,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> FileResponse:
    """Serve a theme asset file."""
    _ = current_user
    path = container.theme_service.resolve_asset_path(theme_id, asset_type)
    return FileResponse(path, media_type="image/png", filename=path.name)


@router.post("/{theme_id}/download")
async def prepare_theme_download(
    theme_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[ThemeDownloadResponse]:
    """Build and return metadata for a downloadable theme asset package."""
    _ = current_user
    result = container.theme_service.get_download_response(theme_id, settings.api_prefix)
    return APIResponse.ok(message="Theme package ready for download", data=result)


@router.get("/{theme_id}/download/file")
async def download_theme_package(
    theme_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> FileResponse:
    """Download the theme asset ZIP package."""
    _ = current_user
    path = container.theme_service.resolve_package_path(theme_id)
    return FileResponse(
        path,
        media_type="application/zip",
        filename=path.name,
    )
