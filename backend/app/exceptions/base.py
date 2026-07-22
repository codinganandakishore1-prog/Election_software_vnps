"""Base exception hierarchy."""

from fastapi import status


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ValidationError(AppException):
    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class NodeOfflineError(AppException):
    def __init__(self, message: str = "Node is offline") -> None:
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)


class ElectionLockedError(AppException):
    def __init__(self, message: str = "Election is locked") -> None:
        super().__init__(message, status.HTTP_409_CONFLICT)


class SynchronizationError(AppException):
    def __init__(self, message: str = "Synchronization failed") -> None:
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class DatabaseConnectionError(AppException):
    def __init__(self, message: str = "Database connection failed") -> None:
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)
