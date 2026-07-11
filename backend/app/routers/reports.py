"""Report generation router (placeholder)."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_reports() -> APIResponse[list]:
    """List generated reports."""
    return APIResponse.ok(data=[])


@router.post("/generate")
async def generate_report() -> APIResponse[dict]:
    """Generate a new report."""
    raise NotImplementedError("Report generation not implemented in scaffold phase.")
