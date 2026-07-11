"""Position schemas (placeholder)."""

from pydantic import BaseModel


class PositionCreate(BaseModel):
    name: str
    election_type: str
    winner_count: int = 1
    display_order: int = 1


class PositionResponse(BaseModel):
    id: str
    position_name: str
    winner_count: int

    model_config = {"from_attributes": True}
