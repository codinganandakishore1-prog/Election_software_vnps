"""Image processing router."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.dependencies.auth import CurrentUser
from app.dependencies.providers import ServiceContainer
from app.schemas.image import CropRequest, ImageResponse, RotateRequest, ZoomRequest

router = APIRouter()


@router.get("/{image_id}")
async def get_image(
    image_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    variant: str = Query(default="processed", description="original, processed, thumbnail, preview, or large"),
) -> FileResponse:
    """Retrieve a candidate image variant."""
    _ = current_user
    path = container.image_service.resolve_image_path(image_id, variant)
    return FileResponse(path, media_type="image/png", filename=path.name)


@router.get("/{image_id}/metadata")
async def get_image_metadata(
    image_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[ImageResponse]:
    """Retrieve image metadata."""
    _ = current_user
    metadata = container.image_service.get_metadata(image_id)
    return APIResponse.ok(data=metadata)


@router.post("/{image_id}/crop")
async def crop_image(
    image_id: str,
    payload: CropRequest,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[ImageResponse]:
    """Crop candidate image."""
    result = container.image_service.crop(image_id, payload, user_id=current_user.id)
    return APIResponse.ok(message="Image cropped successfully", data=result)


@router.post("/{image_id}/rotate")
async def rotate_image(
    image_id: str,
    payload: RotateRequest,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[ImageResponse]:
    """Rotate candidate image."""
    result = container.image_service.rotate(image_id, payload.angle, user_id=current_user.id)
    return APIResponse.ok(message="Image rotated successfully", data=result)


@router.post("/{image_id}/zoom")
async def zoom_image(
    image_id: str,
    payload: ZoomRequest,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[ImageResponse]:
    """Zoom candidate image."""
    result = container.image_service.zoom(image_id, payload.scale, user_id=current_user.id)
    return APIResponse.ok(message="Image zoomed successfully", data=result)


@router.post("/{image_id}/reset")
async def reset_image(
    image_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[ImageResponse]:
    """Restore candidate image to the original upload."""
    result = container.image_service.reset(image_id, user_id=current_user.id)
    return APIResponse.ok(message="Image reset successfully", data=result)
