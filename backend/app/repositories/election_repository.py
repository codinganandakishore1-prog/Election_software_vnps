"""Election repository."""

from election_platform.enums.election import ElectionStatus
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.election import Election
from app.repositories.base import BaseRepository


class ElectionRepository(BaseRepository[Election]):
    """Data access for election records."""

    model = Election

    def list_filtered(
        self,
        *,
        status: ElectionStatus | None = None,
        search: str | None = None,
        active_only: bool = True,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Election]:
        stmt = select(Election)

        if active_only:
            stmt = stmt.where(Election.active.is_(True), Election.deleted_at.is_(None))
        if status is not None:
            stmt = stmt.where(Election.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                Election.election_name.ilike(pattern) | Election.academic_year.ilike(pattern)
            )

        stmt = stmt.order_by(Election.created_at.desc()).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_by_name(self, election_name: str, *, exclude_id: str | None = None) -> Election | None:
        stmt = select(Election).where(
            func.lower(Election.election_name) == election_name.strip().lower(),
            Election.deleted_at.is_(None),
        )
        if exclude_id is not None:
            stmt = stmt.where(Election.id != exclude_id)
        return self.db.scalar(stmt)

    def list_by_status(self, status: ElectionStatus) -> list[Election]:
        return self.list_by_field("status", status)

    def get_latest_by_academic_year(self, academic_year: str) -> Election | None:
        stmt = (
            select(Election)
            .where(Election.academic_year == academic_year, Election.deleted_at.is_(None))
            .order_by(Election.version.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)
