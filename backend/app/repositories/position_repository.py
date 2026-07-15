"""Position repository."""

from election_platform.enums.election import ElectionType
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.position import Position
from app.repositories.base import BaseRepository


class PositionRepository(BaseRepository[Position]):
    """Data access for position records."""

    model = Position

    def list_for_election(self, election_id: str, *, include_inactive: bool = True) -> list[Position]:
        stmt = (
            select(Position)
            .where(Position.election_id == election_id, Position.deleted_at.is_(None))
            .order_by(Position.election_type, Position.display_order)
        )
        if not include_inactive:
            stmt = stmt.where(Position.active.is_(True))
        return list(self.db.scalars(stmt).all())

    def list_by_election_type(
        self,
        election_id: str,
        election_type: ElectionType,
        *,
        include_inactive: bool = True,
    ) -> list[Position]:
        stmt = (
            select(Position)
            .where(
                Position.election_id == election_id,
                Position.election_type == election_type,
                Position.deleted_at.is_(None),
            )
            .order_by(Position.display_order)
        )
        if not include_inactive:
            stmt = stmt.where(Position.active.is_(True))
        return list(self.db.scalars(stmt).all())

    def list_filtered(
        self,
        *,
        election_id: str | None = None,
        election_type: ElectionType | None = None,
        search: str | None = None,
        active: bool | None = None,
    ) -> list[Position]:
        stmt = select(Position).where(Position.deleted_at.is_(None))

        if election_id is not None:
            stmt = stmt.where(Position.election_id == election_id)
        if election_type is not None:
            stmt = stmt.where(Position.election_type == election_type)
        if active is not None:
            stmt = stmt.where(Position.active.is_(active))
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(Position.position_name.ilike(pattern))

        stmt = stmt.order_by(Position.election_type, Position.display_order)
        return list(self.db.scalars(stmt).all())

    def get_by_name(
        self,
        election_id: str,
        election_type: ElectionType,
        position_name: str,
        *,
        exclude_id: str | None = None,
    ) -> Position | None:
        stmt = select(Position).where(
            Position.election_id == election_id,
            Position.election_type == election_type,
            func.lower(Position.position_name) == position_name.strip().lower(),
            Position.deleted_at.is_(None),
        )
        if exclude_id is not None:
            stmt = stmt.where(Position.id != exclude_id)
        return self.db.scalar(stmt)

    def max_display_order(self, election_id: str, election_type: ElectionType) -> int:
        stmt = select(func.coalesce(func.max(Position.display_order), 0)).where(
            Position.election_id == election_id,
            Position.election_type == election_type,
            Position.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0)
