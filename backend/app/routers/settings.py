"""Website settings router."""

from election_platform.enums.roles import UserRole
from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, Depends

from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.providers import ServiceContainer
from app.schemas.settings import (
    DatabaseConnectionResult,
    DatabaseConnectionTest,
    DatabaseSettingsResponse,
    DatabaseSettingsUpdate,
    SystemSettingsResponse,
    SystemSettingsUpdate,
)

router = APIRouter()

AdminUser = Depends(require_roles(UserRole.SUPER_ADMINISTRATOR, UserRole.ADMINISTRATOR))


@router.get("")
async def get_settings(
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[SystemSettingsResponse]:
    """Return website settings."""
    _ = current_user
    settings = container.settings_service.get_system_settings()
    return APIResponse.ok(data=settings)


@router.put("")
async def update_settings(
    payload: SystemSettingsUpdate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[SystemSettingsResponse]:
    """Update website settings."""
    settings = container.settings_service.update_system_settings(payload, user_id=current_user.id)
    return APIResponse.ok(message="Settings updated successfully", data=settings)


@router.get("/database")
async def get_database_settings(
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[DatabaseSettingsResponse]:
    """Return MySQL configuration (masked)."""
    _ = current_user
    settings = container.settings_service.get_database_settings()
    return APIResponse.ok(data=settings)


@router.put("/database")
async def update_database_settings(
    payload: DatabaseSettingsUpdate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[DatabaseSettingsResponse]:
    """Save MySQL connection settings."""
    settings = container.settings_service.update_database_settings(payload, user_id=current_user.id)
    return APIResponse.ok(message="Database settings saved", data=settings)


@router.post("/database/test")
async def test_database_connection(
    payload: DatabaseConnectionTest,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[DatabaseConnectionResult]:
    """Test MySQL connection with supplied credentials."""
    _ = current_user
    result = container.settings_service.test_database_connection(payload)
    return APIResponse.ok(data=result)


@router.post("/database/test-saved")
async def test_saved_database_connection(
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[DatabaseConnectionResult]:
    """Test MySQL connection using saved credentials."""
    _ = current_user
    result = container.settings_service.test_saved_database_connection()
    return APIResponse.ok(data=result)
