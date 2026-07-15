"""User service unit tests."""

from unittest.mock import MagicMock

import pytest

from app.exceptions.base import ValidationError
from app.schemas.user import UserCreate
from app.services.user_service import UserService


def _make_service(**overrides) -> UserService:
    return UserService(
        user_repository=overrides.get("user_repository", MagicMock()),
        audit_log_repository=overrides.get("audit_log_repository", MagicMock()),
        password_hasher=overrides.get("password_hasher", MagicMock()),
    )


def test_create_user_rejects_weak_password() -> None:
    user_repo = MagicMock()
    user_repo.get_by_username.return_value = None
    service = _make_service(user_repository=user_repo)

    with pytest.raises(ValidationError, match="Password must include"):
        service.create_user(
            UserCreate(
                username="viewer1",
                password="weakpass",
                role="Viewer",
            )
        )


def test_create_user_rejects_duplicate_username() -> None:
    user_repo = MagicMock()
    user_repo.get_by_username.return_value = MagicMock()
    service = _make_service(user_repository=user_repo)

    with pytest.raises(ValidationError, match="Username already exists"):
        service.create_user(
            UserCreate(
                username="admin",
                password="SecureP@ss1",
                role="Administrator",
            )
        )
