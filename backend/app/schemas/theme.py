"""Theme and branding schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ThemeBase(BaseModel):
    """Shared theme fields."""

    theme_name: str = Field(..., min_length=1, max_length=100)
    school_name: str | None = Field(default=None, max_length=255)
    font_heading: str | None = Field(default=None, max_length=100)
    font_body: str | None = Field(default=None, max_length=100)
    font_accent: str | None = Field(default=None, max_length=100)
    primary_color: str | None = Field(default=None, max_length=20)
    secondary_color: str | None = Field(default=None, max_length=20)
    accent_color: str | None = Field(default=None, max_length=20)
    warning_color: str | None = Field(default=None, max_length=20)
    danger_color: str | None = Field(default=None, max_length=20)
    background_color: str | None = Field(default=None, max_length=20)
    surface_color: str | None = Field(default=None, max_length=20)
    text_primary_color: str | None = Field(default=None, max_length=20)
    text_secondary_color: str | None = Field(default=None, max_length=20)


class ThemeCreate(ThemeBase):
    """Create a new theme."""

    pass


class ThemeUpdate(BaseModel):
    """Update theme metadata and colors."""

    theme_name: str | None = Field(default=None, min_length=1, max_length=100)
    school_name: str | None = Field(default=None, max_length=255)
    font_heading: str | None = Field(default=None, max_length=100)
    font_body: str | None = Field(default=None, max_length=100)
    font_accent: str | None = Field(default=None, max_length=100)
    primary_color: str | None = Field(default=None, max_length=20)
    secondary_color: str | None = Field(default=None, max_length=20)
    accent_color: str | None = Field(default=None, max_length=20)
    warning_color: str | None = Field(default=None, max_length=20)
    danger_color: str | None = Field(default=None, max_length=20)
    background_color: str | None = Field(default=None, max_length=20)
    surface_color: str | None = Field(default=None, max_length=20)
    text_primary_color: str | None = Field(default=None, max_length=20)
    text_secondary_color: str | None = Field(default=None, max_length=20)


class ThemeResponse(ThemeBase):
    """Theme record returned by the API."""

    id: str
    active: bool
    school_logo_path: str | None = None
    election_logo_path: str | None = None
    background_light_path: str | None = None
    background_dark_path: str | None = None
    background_welcome_path: str | None = None
    icon_app_path: str | None = None
    icon_favicon_path: str | None = None
    logo_path: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ThemeAssetUploadResponse(BaseModel):
    """Response after uploading a theme asset."""

    theme_id: str
    asset_type: str
    path: str


class ThemeDownloadResponse(BaseModel):
    """Downloadable theme package metadata."""

    theme_id: str
    filename: str
    download_url: str
    checksum: str
    package_size: int
