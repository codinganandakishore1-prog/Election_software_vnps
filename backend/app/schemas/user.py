"""User management schemas."""

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=150)
    email: str | None = Field(default=None, max_length=150)
    role: str


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=150)
    email: str | None = Field(default=None, max_length=150)
    role: str | None = None
    active: bool | None = None


class UserProfileUpdate(BaseModel):
    """Self-service profile fields (no role/status changes)."""

    full_name: str | None = Field(default=None, max_length=150)
    email: str | None = Field(default=None, max_length=150)


class UserPasswordReset(BaseModel):
    password: str = Field(..., min_length=8, max_length=128)


class UserPasswordChange(BaseModel):
    old_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str | None = None
    email: str | None = None
    role: str
    active: bool

    model_config = {"from_attributes": True}
