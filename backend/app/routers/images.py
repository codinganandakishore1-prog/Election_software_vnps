"""Image processing router (placeholder)."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter

router = APIRouter()


@router.get("/{image_id}")
async def get_image(image_id: str) -> APIResponse[dict]:
    """Retrieve image metadata."""
    return APIResponse.ok(data={"id": image_id})


@router.post("/{image_id}/crop")
async def crop_image(image_id: str) -> APIResponse[dict]:
    """Crop candidate image."""
    raise NotImplementedError("Image crop not implemented in scaffold phase.")
