"""Election schemas (placeholder)."""

from pydantic import BaseModel


class ElectionCreate(BaseModel):
    name: str
    academic_year: str | None = None
    description: str | None = None


class ElectionResponse(BaseModel):
    id: str
    name: str
    version: int
    status: str

    model_config = {"from_attributes": True}
