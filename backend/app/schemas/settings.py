"""Website settings request/response schemas."""

from pydantic import BaseModel, Field


class SystemSettingsResponse(BaseModel):
    """Website-wide configuration."""

    id: str | None = None
    school_name: str | None = None
    school_logo: str | None = None
    election_logo: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    timezone: str | None = None
    maintenance_mode: bool = False


class SystemSettingsUpdate(BaseModel):
    """Payload for updating website settings."""

    school_name: str | None = Field(default=None, max_length=255)
    school_logo: str | None = Field(default=None, max_length=255)
    election_logo: str | None = Field(default=None, max_length=255)
    primary_color: str | None = Field(default=None, max_length=20)
    secondary_color: str | None = Field(default=None, max_length=20)
    timezone: str | None = Field(default=None, max_length=100)
    maintenance_mode: bool | None = None


class DatabaseSettingsResponse(BaseModel):
    """MySQL connection settings with masked password."""

    id: str | None = None
    host: str | None = None
    port: int = 3306
    database_name: str | None = None
    username: str | None = None
    password_configured: bool = False


class DatabaseSettingsUpdate(BaseModel):
    """Payload for updating MySQL connection settings."""

    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(default=3306, ge=1, le=65535)
    database_name: str = Field(..., min_length=1, max_length=150)
    username: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=1)


class DatabaseConnectionTest(BaseModel):
    """Payload for testing a MySQL connection."""

    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(default=3306, ge=1, le=65535)
    database_name: str = Field(..., min_length=1, max_length=150)
    username: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=1)


class DatabaseConnectionResult(BaseModel):
    """Result of a database connectivity test."""

    success: bool
    message: str
