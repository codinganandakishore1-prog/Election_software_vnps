"""Configuration download router."""

from pathlib import Path

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.dependencies.auth import CurrentUser
from app.dependencies.providers import ServiceContainer
from app.schemas.election import PublishedVersionResponse

router = APIRouter()


@router.get("/package")
async def download_configuration_package(
    current_user: CurrentUser,
    container: ServiceContainer,
    election_id: str,
) -> FileResponse:
    """Download the latest published election configuration package."""
    _ = current_user
    record = container.election_service.get_latest_configuration(election_id)
    if record is None:
        raise HTTPException(status_code=404, detail="No published configuration found")

    package_path = Path(record.package_path)
    if not package_path.exists():
        raise HTTPException(status_code=404, detail="Configuration package file not found")

    return FileResponse(
        path=package_path,
        media_type="application/zip",
        filename=package_path.name,
    )


@router.post("/checksum")
async def verify_checksum(
    current_user: CurrentUser,
    container: ServiceContainer,
    election_id: str = Query(...),
    checksum: str = Query(...),
) -> APIResponse[dict]:
    """Verify package checksum against the latest published configuration."""
    _ = current_user
    record = container.election_service.get_latest_configuration(election_id)
    if record is None:
        return APIResponse.ok(data={"valid": False, "reason": "No published configuration"})

    valid = record.checksum.lower() == checksum.strip().lower()
    return APIResponse.ok(data={"valid": valid, "expected": record.checksum})
