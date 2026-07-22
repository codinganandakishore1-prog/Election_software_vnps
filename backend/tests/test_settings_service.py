"""Settings service unit tests."""

from unittest.mock import MagicMock

import pytest

from app.exceptions.base import ValidationError
from app.models.settings import SystemSettings
from app.schemas.settings import DatabaseConnectionTest, SystemSettingsUpdate
from app.security.secret_cipher import SecretCipher
from app.services.settings_service import SettingsService


def _make_service(**overrides) -> SettingsService:
    settings_repo = overrides.get("settings_repository", MagicMock())
    mysql_repo = overrides.get("mysql_settings_repository", MagicMock())
    audit_repo = overrides.get("audit_log_repository", MagicMock())
    cipher = overrides.get("secret_cipher", SecretCipher("test-secret-key"))
    return SettingsService(settings_repo, mysql_repo, audit_repo, secret_cipher=cipher)


def test_get_system_settings_returns_defaults_when_missing() -> None:
    settings_repo = MagicMock()
    settings_repo.get_active.return_value = None
    service = _make_service(settings_repository=settings_repo)

    result = service.get_system_settings()
    assert result.school_name is None
    assert result.maintenance_mode is False


def test_update_system_settings_creates_record() -> None:
    settings_repo = MagicMock()
    settings_repo.get_active.return_value = None
    service = _make_service(settings_repository=settings_repo)

    result = service.update_system_settings(
        SystemSettingsUpdate(school_name="VNPS", timezone="UTC"),
        user_id="user-1",
    )
    assert result.school_name == "VNPS"
    settings_repo.add.assert_called_once()
    settings_repo.commit.assert_called_once()


def test_update_system_settings_updates_existing_record() -> None:
    existing = SystemSettings(id="settings-1", school_name="Old Name", maintenance_mode=False)
    settings_repo = MagicMock()
    settings_repo.get_active.return_value = existing
    service = _make_service(settings_repository=settings_repo)

    result = service.update_system_settings(SystemSettingsUpdate(school_name="New Name"))
    assert result.school_name == "New Name"
    settings_repo.add.assert_not_called()


def test_test_saved_database_connection_requires_saved_settings() -> None:
    mysql_repo = MagicMock()
    mysql_repo.get_latest.return_value = None
    service = _make_service(mysql_settings_repository=mysql_repo)

    with pytest.raises(ValidationError, match="No database settings"):
        service.test_saved_database_connection()


def test_test_database_connection_reports_failure() -> None:
    service = _make_service()
    result = service.test_database_connection(
        DatabaseConnectionTest(
            host="invalid-host",
            port=3306,
            database_name="missing",
            username="root",
            password="secret",
        )
    )
    assert result.success is False
    assert result.message
