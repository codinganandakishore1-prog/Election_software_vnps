"""Configuration download router."""

from pathlib import Path

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse

from app.dependencies.providers import ServiceContainer
from app.security.jwt import JWTHandler

router = APIRouter()


def _require_download_auth(request: Request) -> None:
    """Allow either administrator access tokens or voting-node tokens."""
    claims = getattr(request.state, "auth_claims", None)
    if not isinstance(claims, dict):
        raise HTTPException(status_code=401, detail="Authentication required")
    token_type = claims.get("type")
    if token_type not in {JWTHandler.TOKEN_TYPE_ACCESS, JWTHandler.TOKEN_TYPE_NODE}:
        raise HTTPException(status_code=403, detail="Invalid token type for configuration download")


@router.get("/package")
async def download_configuration_package(
    request: Request,
    container: ServiceContainer,
    election_id: str,
) -> FileResponse:
    """Download the latest published election configuration package."""
    _require_download_auth(request)
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
    request: Request,
    container: ServiceContainer,
    election_id: str = Query(...),
    checksum: str = Query(...),
) -> APIResponse[dict]:
    """Verify package checksum against the latest published configuration."""
    _require_download_auth(request)
    record = container.election_service.get_latest_configuration(election_id)
    if record is None:
        return APIResponse.ok(data={"valid": False, "reason": "No published configuration"})

    valid = record.checksum.lower() == checksum.strip().lower()
    return APIResponse.ok(data={"valid": valid, "expected": record.checksum})
