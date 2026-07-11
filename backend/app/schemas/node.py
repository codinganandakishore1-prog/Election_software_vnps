"""Node schemas (placeholder)."""

from pydantic import BaseModel


class HeartbeatRequest(BaseModel):
    node_id: str
    app_version: str
    config_version: int
    queue_size: int = 0


class NodeResponse(BaseModel):
    id: str
    node_name: str
    election_type: str

    model_config = {"from_attributes": True}
