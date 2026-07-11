"""Custom application exceptions."""

from app.exceptions.base import (
    AppException,
    AuthenticationError,
    DatabaseConnectionError,
    ElectionLockedError,
    NodeOfflineError,
    SynchronizationError,
    ValidationError,
)

__all__ = [
    "AppException",
    "AuthenticationError",
    "DatabaseConnectionError",
    "ElectionLockedError",
    "NodeOfflineError",
    "SynchronizationError",
    "ValidationError",
]
