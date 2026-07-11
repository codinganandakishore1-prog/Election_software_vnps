"""Synchronization schemas (placeholder)."""

from pydantic import BaseModel


class VotePayload(BaseModel):
    vote_uuid: str
    candidate_id: str
    position_id: str
    timestamp: str


class VoteUploadRequest(BaseModel):
    node_id: str
    config_version: int
    votes: list[VotePayload]


class SyncResponse(BaseModel):
    accepted: int = 0
    duplicates: int = 0
    failed: int = 0
