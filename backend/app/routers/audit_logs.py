"""Audit log query router."""

from datetime import datetime

from election_platform.enums.roles import UserRole
from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.providers import ServiceContainer
from app.schemas.audit_log import AuditLogPageResponse

router = APIRouter()

ViewerUser = Depends(
    require_roles(
        UserRole.SUPER_ADMINISTRATOR,
        UserRole.ADMINISTRATOR,
        UserRole.VIEWER,
    )
)


@router.get("")
async def list_audit_logs(
    current_user: CurrentUser,
    container: ServiceContainer,
    module: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    _: None = ViewerUser,
) -> APIResponse[AuditLogPageResponse]:
    """List audit logs with filtering and full-text search."""
    _ = current_user
    result = container.audit_log_service.list_audit_logs(
        module=module,
        user_id=user_id,
        action=action,
        search=search,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return APIResponse.ok(data=result)


@router.get("/modules")
async def list_audit_modules(
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = ViewerUser,
) -> APIResponse[list[str]]:
    """Return known audit module names for filter controls."""
    _ = current_user
    return APIResponse.ok(data=container.audit_log_service.list_modules())
