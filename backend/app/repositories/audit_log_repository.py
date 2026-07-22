"""Audit log repository."""

from datetime import datetime

from sqlalchemy import func, or_, select

from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Data access for immutable audit logs."""

    model = AuditLog

    def list_for_user(self, user_id: str, *, limit: int | None = None) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())

    def list_for_module(self, module: str, *, limit: int | None = None) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.module == module)
            .order_by(AuditLog.created_at.desc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())

    def search(
        self,
        *,
        module: str | None = None,
        user_id: str | None = None,
        action: str | None = None,
        search: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Search audit logs with optional filters and pagination."""
        stmt = select(AuditLog)
        count_stmt = select(func.count()).select_from(AuditLog)

        if module:
            stmt = stmt.where(AuditLog.module == module)
            count_stmt = count_stmt.where(AuditLog.module == module)

        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
            count_stmt = count_stmt.where(AuditLog.user_id == user_id)

        if action:
            pattern = f"%{action.strip()}%"
            stmt = stmt.where(AuditLog.action.ilike(pattern))
            count_stmt = count_stmt.where(AuditLog.action.ilike(pattern))

        if from_date is not None:
            stmt = stmt.where(AuditLog.created_at >= from_date)
            count_stmt = count_stmt.where(AuditLog.created_at >= from_date)

        if to_date is not None:
            stmt = stmt.where(AuditLog.created_at <= to_date)
            count_stmt = count_stmt.where(AuditLog.created_at <= to_date)

        if search and search.strip():
            term = f"%{search.strip()}%"
            user_match = (
                select(AuditLog.id)
                .join(User, AuditLog.user_id == User.id, isouter=True)
                .where(
                    or_(
                        AuditLog.action.ilike(term),
                        AuditLog.module.ilike(term),
                        User.username.ilike(term),
                        User.full_name.ilike(term),
                    )
                )
            )
            stmt = stmt.where(AuditLog.id.in_(user_match))
            count_stmt = count_stmt.where(AuditLog.id.in_(user_match))

        total = self.db.scalar(count_stmt) or 0
        rows = list(
            self.db.scalars(
                stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
            ).all()
        )
        return rows, total
