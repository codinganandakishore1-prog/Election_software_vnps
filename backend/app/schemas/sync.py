"""Synchronization request and response schemas."""

from pydantic import BaseModel, Field


class VotePayload(BaseModel):
    """Single vote within a synchronization batch."""

    vote_uuid: str
    election_id: str
    position_id: str
    candidate_id: str
    election_type: str
    house_id: str | None = None
    timestamp: str


class VoteUploadRequest(BaseModel):
    """Batch vote upload from a voting node."""

    node_id: str
    config_version: int
    votes: list[VotePayload] = Field(default_factory=list)


class SyncResponse(BaseModel):
    """Per-UUID acknowledgment for a vote upload batch."""

    success: bool = True
    accepted: list[str] = Field(default_factory=list)
    duplicates: list[str] = Field(default_factory=list)
    failed: list[str] = Field(default_factory=list)


class SyncVersionResponse(BaseModel):
    """Configuration version check response."""

    latest_version: int = 0
    download_required: bool = False
