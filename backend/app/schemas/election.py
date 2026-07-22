"""Election request/response schemas."""

from datetime import datetime

from election_platform.enums.election import ElectionStatus
from pydantic import BaseModel, Field


class ElectionCreate(BaseModel):
    """Payload for creating an election."""

    name: str = Field(..., min_length=1, max_length=200)
    academic_year: str | None = Field(default=None, max_length=20)
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class ElectionUpdate(BaseModel):
    """Payload for updating election metadata."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    academic_year: str | None = Field(default=None, max_length=20)
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    logo_path: str | None = Field(default=None, max_length=255)


class ElectionSummaryResponse(BaseModel):
    """Election list item."""

    id: str
    name: str
    academic_year: str | None
    version: int
    status: ElectionStatus
    configuration_locked: bool
    position_count: int = 0
    candidate_count: int = 0
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ElectionDetailResponse(ElectionSummaryResponse):
    """Full election details."""

    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    logo_path: str | None = None
    created_by: str | None = None
    regular_position_count: int = 0
    house_position_count: int = 0
    latest_checksum: str | None = None


class ElectionValidationResponse(BaseModel):
    """Pre-publish validation result."""

    valid: bool
    errors: list[str] = Field(default_factory=list)


class ElectionPublishResponse(BaseModel):
    """Publish operation result."""

    election_id: str
    version: int
    checksum: str
    package_path: str


class PublishedVersionResponse(BaseModel):
    """Published configuration version metadata."""

    id: str
    version: int
    checksum: str
    package_path: str
    published_at: datetime
    published_by: str | None = None
    package_size: int | None = None

    model_config = {"from_attributes": True}


class ElectionLockResponse(BaseModel):
    """Lock status for an election."""

    election_id: str
    configuration_locked: bool
    status: ElectionStatus
    message: str


class ElectionDuplicateRequest(BaseModel):
    """Optional name override when duplicating."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
