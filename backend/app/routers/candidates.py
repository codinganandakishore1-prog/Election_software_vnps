"""Candidate management router (placeholder)."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter

from app.schemas.candidate import CandidateCreate, CandidateResponse

router = APIRouter()


@router.get("")
async def list_candidates() -> APIResponse[list[CandidateResponse]]:
    """List all candidates."""
    return APIResponse.ok(data=[])


@router.get("/{candidate_id}")
async def get_candidate(candidate_id: str) -> APIResponse[dict]:
    """Get candidate details."""
    return APIResponse.ok(data={"id": candidate_id})


@router.post("")
async def create_candidate(_payload: CandidateCreate) -> APIResponse[dict]:
    """Create a new candidate."""
    raise NotImplementedError("Candidate creation not implemented in scaffold phase.")
