"""Candidate schemas (placeholder)."""

from pydantic import BaseModel


class CandidateCreate(BaseModel):
    candidate_name: str
    position_id: str
    house_id: str | None = None
    display_order: int = 1


class CandidateResponse(BaseModel):
    id: str
    candidate_name: str
    status: str

    model_config = {"from_attributes": True}
