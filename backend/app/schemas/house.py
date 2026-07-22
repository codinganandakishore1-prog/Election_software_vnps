"""House management schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class HouseResponse(BaseModel):
    """Full house record."""

    id: str
    house_name: str
    color: str | None = None
    logo_path: str | None = None
    active: bool

    model_config = {"from_attributes": True}


class HouseConfigurationRequest(BaseModel):
    """Configure shared house leadership positions for an election."""

    election_id: str
    positions: list[str] = Field(..., min_length=1, max_length=10)


class HousePositionSummary(BaseModel):
    """House position with candidate coverage per house."""

    id: str
    position_name: str
    display_order: int
    winner_count: int
    active: bool
    candidate_count_by_house: dict[str, int] = Field(default_factory=dict)


class HouseConfigurationResponse(BaseModel):
    """Current house election configuration."""

    election_id: str
    positions: list[HousePositionSummary]
    houses: list[HouseResponse]


class HouseCandidateCreate(BaseModel):
    """Create a house election candidate."""

    election_id: str
    position_id: str
    house_id: str
    candidate_name: str = Field(..., min_length=1, max_length=150)
    candidate_class: str | None = Field(default=None, max_length=50)
    candidate_section: str | None = Field(default=None, max_length=50)
    display_order: int = Field(default=1, ge=1)


class HouseCandidateUpdate(BaseModel):
    """Update a house election candidate."""

    candidate_name: str | None = Field(default=None, min_length=1, max_length=150)
    position_id: str | None = None
    house_id: str | None = None
    candidate_class: str | None = Field(default=None, max_length=50)
    candidate_section: str | None = Field(default=None, max_length=50)
    display_order: int | None = Field(default=None, ge=1)


class HouseCandidateResponse(BaseModel):
    """House candidate returned by the API."""

    id: str
    election_id: str
    position_id: str
    position_name: str
    house_id: str
    house_name: str
    candidate_name: str
    candidate_class: str | None = None
    candidate_section: str | None = None
    display_order: int
    status: str
    has_image: bool
    created_at: datetime
    updated_at: datetime


class NodeAssignmentUpdate(BaseModel):
    """Update voting node house assignment."""

    node_name: str | None = Field(default=None, min_length=1, max_length=100)
    election_type: str | None = None
    house_id: str | None = None
    active: bool | None = None


class NodeAssignmentResponse(BaseModel):
    """Voting node with house assignment details."""

    id: str
    node_name: str
    election_type: str
    house_id: str | None = None
    house_name: str | None = None
    active: bool
    config_version: int

    model_config = {"from_attributes": True}


class HouseValidationResponse(BaseModel):
    """Result of house configuration and assignment validation."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
