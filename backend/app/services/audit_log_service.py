"""Audit log query service."""

from __future__ import annotations

from datetime import datetime

from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from app.schemas.audit_log import AuditLogPageResponse, AuditLogResponse
from app.services.base import BaseService

# Canonical module names used across services when writing audit entries.
AUDIT_MODULES: tuple[str, ...] = (
    "Authentication",
    "Elections",
    "Positions",
    "Candidates",
    "Houses",
    "Nodes",
    "Synchronization",
    "Reports",
    "Images",
    "Themes",
    "Settings",
    "Users",
)


class AuditLogService(BaseService):
    """Read-only access to immutable audit logs with filtering and search."""

    def __init__(
        self,
        audit_log_repository: AuditLogRepository,
        user_repository: UserRepository,
    ) -> None:
        self.audit_log_repository = audit_log_repository
        self.user_repository = user_repository

    def list_modules(self) -> list[str]:
        """Return known audit module names for filter dropdowns."""
        return list(AUDIT_MODULES)

    def list_audit_logs(
        self,
        *,
        module: str | None = None,
        user_id: str | None = None,
        action: str | None = None,
        search: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> AuditLogPageResponse:
        offset = (page - 1) * page_size
        rows, total = self.audit_log_repository.search(
            module=module,
            user_id=user_id,
            action=action,
            search=search,
            from_date=from_date,
            to_date=to_date,
            offset=offset,
            limit=page_size,
        )
        user_names = self._resolve_user_names({row.user_id for row in rows if row.user_id})
        items = [self._to_response(row, user_names) for row in rows]
        return AuditLogPageResponse(items=items, total=total, page=page, page_size=page_size)

    def _resolve_user_names(self, user_ids: set[str]) -> dict[str, str]:
        names: dict[str, str] = {}
        for user_id in user_ids:
            user = self.user_repository.get_by_id(user_id)
            if user is None:
                continue
            names[user_id] = user.full_name or user.username
        return names

    @staticmethod
    def _to_response(row: AuditLog, user_names: dict[str, str]) -> AuditLogResponse:
        user_name = user_names.get(row.user_id) if row.user_id else None
        return AuditLogResponse(
            id=row.id,
            user_id=row.user_id,
            user_name=user_name,
            module=row.module,
            action=row.action,
            old_value=row.old_value,
            new_value=row.new_value,
            ip_address=row.ip_address,
            browser=row.browser,
            created_at=row.created_at,
        )
