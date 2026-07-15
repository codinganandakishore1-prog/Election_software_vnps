"""Candidate schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class CandidateCreate(BaseModel):
    """Create a candidate for regular or house elections."""

    election_id: str
    candidate_name: str = Field(..., min_length=1, max_length=150)
    position_id: str
    house_id: str | None = None
    candidate_class: str | None = Field(default=None, max_length=50)
    candidate_section: str | None = Field(default=None, max_length=50)
    display_order: int = Field(default=1, ge=1)


class CandidateUpdate(BaseModel):
    """Update candidate details."""

    candidate_name: str | None = Field(default=None, min_length=1, max_length=150)
    position_id: str | None = None
    house_id: str | None = None
    candidate_class: str | None = Field(default=None, max_length=50)
    candidate_section: str | None = Field(default=None, max_length=50)
    display_order: int | None = Field(default=None, ge=1)


class CandidateResponse(BaseModel):
    """Candidate record returned by the API."""

    id: str
    election_id: str
    candidate_name: str
    position_id: str
    position_name: str
    house_id: str | None = None
    house_name: str | None = None
    election_type: str
    candidate_class: str | None = None
    candidate_section: str | None = None
    display_order: int
    status: str
    has_image: bool
    image_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
