"""Website settings service."""

from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.database.base import utc_now
from app.database.seeds import new_uuid
from app.exceptions.base import ValidationError
from app.models.audit_log import AuditLog
from app.models.settings import MySQLSettings, SystemSettings
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.settings_repository import MySQLSettingsRepository, SettingsRepository
from app.schemas.settings import (
    DatabaseConnectionResult,
    DatabaseConnectionTest,
    DatabaseSettingsResponse,
    DatabaseSettingsUpdate,
    SystemSettingsResponse,
    SystemSettingsUpdate,
)
from app.security.secret_cipher import SecretCipher
from app.services.base import BaseService


class SettingsService(BaseService):
    """Handles website and database settings."""

    def __init__(
        self,
        settings_repository: SettingsRepository,
        mysql_settings_repository: MySQLSettingsRepository,
        audit_log_repository: AuditLogRepository,
        secret_cipher: SecretCipher | None = None,
    ) -> None:
        self.settings_repository = settings_repository
        self.mysql_settings_repository = mysql_settings_repository
        self.audit_log_repository = audit_log_repository
        self.secret_cipher = secret_cipher or SecretCipher()

    def get_system_settings(self) -> SystemSettingsResponse:
        settings = self.settings_repository.get_active()
        if settings is None:
            return SystemSettingsResponse()
        return self._to_system_response(settings)

    def update_system_settings(
        self,
        payload: SystemSettingsUpdate,
        *,
        user_id: str | None = None,
    ) -> SystemSettingsResponse:
        settings = self.settings_repository.get_active()
        if settings is None:
            settings = SystemSettings(id=new_uuid(), maintenance_mode=False)
            self.settings_repository.add(settings)

        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(settings, field, value)

        self._audit(user_id, "Settings Updated", "settings", updates)
        self.settings_repository.commit()
        return self._to_system_response(settings)

    def get_database_settings(self) -> DatabaseSettingsResponse:
        record = self.mysql_settings_repository.get_latest()
        if record is None:
            return DatabaseSettingsResponse()
        return DatabaseSettingsResponse(
            id=record.id,
            host=record.host,
            port=record.port,
            database_name=record.database_name,
            username=record.username,
            password_configured=bool(record.encrypted_password),
        )

    def update_database_settings(
        self,
        payload: DatabaseSettingsUpdate,
        *,
        user_id: str | None = None,
    ) -> DatabaseSettingsResponse:
        record = MySQLSettings(
            id=new_uuid(),
            host=payload.host.strip(),
            port=payload.port,
            database_name=payload.database_name.strip(),
            username=payload.username.strip(),
            encrypted_password=self.secret_cipher.encrypt(payload.password),
            updated_by=user_id,
            updated_at=utc_now(),
        )
        self.mysql_settings_repository.add(record)
        self._audit(
            user_id,
            "Database Settings Updated",
            "settings",
            {
                "host": record.host,
                "port": record.port,
                "database_name": record.database_name,
                "username": record.username,
            },
        )
        self.mysql_settings_repository.commit()
        return DatabaseSettingsResponse(
            id=record.id,
            host=record.host,
            port=record.port,
            database_name=record.database_name,
            username=record.username,
            password_configured=True,
        )

    def test_database_connection(self, payload: DatabaseConnectionTest) -> DatabaseConnectionResult:
        url = (
            f"mysql+pymysql://{payload.username}:{payload.password}"
            f"@{payload.host}:{payload.port}/{payload.database_name}"
        )
        try:
            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return DatabaseConnectionResult(success=True, message="Connection successful")
        except SQLAlchemyError as exc:
            return DatabaseConnectionResult(success=False, message=str(exc))
        except Exception as exc:  # noqa: BLE001
            return DatabaseConnectionResult(success=False, message=str(exc))

    def test_saved_database_connection(self) -> DatabaseConnectionResult:
        record = self.mysql_settings_repository.get_latest()
        if record is None:
            raise ValidationError("No database settings have been saved")

        try:
            password = self.secret_cipher.decrypt(record.encrypted_password)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        return self.test_database_connection(
            DatabaseConnectionTest(
                host=record.host,
                port=record.port,
                database_name=record.database_name,
                username=record.username,
                password=password,
            )
        )

    @staticmethod
    def _to_system_response(settings: SystemSettings) -> SystemSettingsResponse:
        return SystemSettingsResponse(
            id=settings.id,
            school_name=settings.school_name,
            school_logo=settings.school_logo,
            election_logo=settings.election_logo,
            primary_color=settings.primary_color,
            secondary_color=settings.secondary_color,
            timezone=settings.timezone,
            maintenance_mode=settings.maintenance_mode,
        )

    def _audit(
        self,
        user_id: str | None,
        action: str,
        module: str,
        details: dict | None = None,
    ) -> None:
        self.audit_log_repository.add(
            AuditLog(
                id=new_uuid(),
                user_id=user_id,
                action=action,
                module=module,
                new_value=str(details) if details else None,
            )
        )
