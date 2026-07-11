"""Authentication schemas (placeholder)."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class NodeLoginRequest(BaseModel):
    node_id: str
    node_secret: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    expires_in: int = Field(default=3600)
