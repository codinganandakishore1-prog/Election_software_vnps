"""Configuration download router (placeholder)."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter

router = APIRouter()


@router.get("/package")
async def download_configuration_package() -> APIResponse[dict]:
    """Download published election configuration package."""
    raise NotImplementedError("Configuration download not implemented in scaffold phase.")


@router.post("/checksum")
async def verify_checksum() -> APIResponse[dict]:
    """Verify package checksum."""
    return APIResponse.ok(data={"valid": True})
