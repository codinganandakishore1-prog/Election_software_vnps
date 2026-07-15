"""Candidate image request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class CropRequest(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class RotateRequest(BaseModel):
    angle: int = Field(description="Rotation angle in degrees (multiples of 90)")


class ZoomRequest(BaseModel):
    scale: float = Field(ge=0.25, le=4.0, description="Zoom scale between 25% and 400%")


class ImageUploadResponse(BaseModel):
    image_id: str
    candidate_id: str


class ImageResponse(BaseModel):
    id: str
    original_path: str | None = None
    processed_path: str | None = None
    thumbnail_path: str | None = None
    width: int | None = None
    height: int | None = None
    file_size: int | None = None
    mime_type: str | None = None
    uploaded_at: datetime | None = None

    model_config = {"from_attributes": True}
