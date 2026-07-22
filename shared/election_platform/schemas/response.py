"""Standard API response schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Validation error detail."""

    field: str
    message: str


class APIResponse(BaseModel, Generic[T]):
    """Standardized REST API response envelope."""

    success: bool = True
    message: str = "Operation completed successfully"
    data: T | None = None
    errors: list[ErrorDetail] = Field(default_factory=list)

    @classmethod
    def ok(cls, message: str = "Operation completed successfully", data: Any = None) -> "APIResponse[Any]":
        return cls(success=True, message=message, data=data)

    @classmethod
    def fail(cls, message: str, errors: list[ErrorDetail] | None = None) -> "APIResponse[Any]":
        return cls(success=False, message=message, errors=errors or [])
