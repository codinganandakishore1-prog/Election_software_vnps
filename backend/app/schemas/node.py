"""Node schemas."""

from datetime import datetime

from election_platform.enums.sync import SyncStatus
from pydantic import BaseModel, Field

from app.schemas.house import NodeAssignmentResponse, NodeAssignmentUpdate

__all__ = [
    "HeartbeatRequest",
    "HeartbeatResponse",
    "NodeAssignmentResponse",
    "NodeAssignmentUpdate",
    "NodeCreate",
    "NodeHealthResponse",
    "NodeRegistrationResponse",
    "NodeResponse",
    "NodeUpdate",
]


class NodeCreate(BaseModel):
    """Register a new voting node."""

    node_name: str = Field(..., min_length=1, max_length=100)
    election_type: str
    house_id: str | None = None
    active: bool = True


class NodeRegistrationResponse(BaseModel):
    """Newly registered node; secret is returned once at creation."""

    id: str
    node_name: str
    election_type: str
    house_id: str | None = None
    house_name: str | None = None
    active: bool
    config_version: int
    node_secret: str

    model_config = {"from_attributes": True}


class HeartbeatRequest(BaseModel):
    """Desktop node heartbeat payload."""

    node_id: str
    app_version: str
    config_version: int
    queue_size: int = 0
    last_vote_time: datetime | None = None
    sync_status: SyncStatus = SyncStatus.HEALTHY


class HeartbeatResponse(BaseModel):
    """Heartbeat acknowledgement."""

    server_time: datetime
    status: str
    node_name: str


class NodeResponse(BaseModel):
    """Voting node with monitoring metadata."""

    id: str
    node_name: str
    election_type: str
    house_id: str | None = None
    house_name: str | None = None
    active: bool
    config_version: int
    app_version: str | None = None
    status: str
    queue_size: int = 0
    sync_status: str | None = None
    last_heartbeat: datetime | None = None
    last_vote_time: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NodeHealthResponse(BaseModel):
    """Node health snapshot from latest heartbeat."""

    node_id: str
    node_name: str
    status: str
    last_heartbeat: datetime | None = None
    queue_size: int = 0
    sync_status: str | None = None
    last_vote_time: datetime | None = None
    app_version: str | None = None
    config_version: int


class NodeUpdate(NodeAssignmentUpdate):
    """Alias for node assignment updates."""

    node_name: str | None = Field(default=None, min_length=1, max_length=100)
