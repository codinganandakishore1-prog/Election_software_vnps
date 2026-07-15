"""Position request/response schemas."""

from datetime import datetime

from election_platform.enums.election import ElectionType
from pydantic import BaseModel, Field


class PositionCreate(BaseModel):
    """Payload for creating a position."""

    election_id: str
    name: str = Field(..., min_length=1, max_length=150)
    election_type: ElectionType
    winner_count: int = Field(default=1, ge=1)
    display_order: int | None = Field(default=None, ge=1)


class PositionUpdate(BaseModel):
    """Payload for updating a position."""

    name: str | None = Field(default=None, min_length=1, max_length=150)
    winner_count: int | None = Field(default=None, ge=1)
    display_order: int | None = Field(default=None, ge=1)


class PositionResponse(BaseModel):
    """Position record returned by the API."""

    id: str
    election_id: str
    position_name: str
    election_type: ElectionType
    winner_count: int
    display_order: int
    active: bool
    candidate_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PositionReorderRequest(BaseModel):
    """Bulk reorder payload."""

    election_id: str
    election_type: ElectionType
    ordered_ids: list[str] = Field(..., min_length=1)
