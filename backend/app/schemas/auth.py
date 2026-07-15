"""Authentication request/response schemas."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class NodeLoginRequest(BaseModel):
    node_id: str
    node_secret: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    expires_in: int = Field(default=3600)
    token_type: str = "bearer"
    role: str | None = None
    username: str | None = None
    full_name: str | None = None
    user_id: str | None = None
    email: str | None = None


class RefreshResponse(BaseModel):
    access_token: str
    expires_in: int
    token_type: str = "bearer"


class VerifyResponse(BaseModel):
    valid: bool
    expires_in: int | None = None
    username: str | None = None
    role: str | None = None


class AuthenticatedUserResponse(BaseModel):
    id: str
    username: str
    full_name: str | None = None
    email: str | None = None
    role: str

    model_config = {"from_attributes": True}
