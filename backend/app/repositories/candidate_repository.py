"""Candidate repository."""

from election_platform.enums.election import CandidateStatus, ElectionType
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.candidate import Candidate, CandidateImage
from app.models.position import Position
from app.repositories.base import BaseRepository


class CandidateRepository(BaseRepository[Candidate]):
    """Data access for candidate records."""

    model = Candidate

    def list_for_position(self, position_id: str) -> list[Candidate]:
        stmt = (
            select(Candidate)
            .where(Candidate.position_id == position_id, Candidate.deleted_at.is_(None))
            .order_by(Candidate.display_order)
        )
        return list(self.db.scalars(stmt).all())

    def list_for_election(self, election_id: str) -> list[Candidate]:
        stmt = (
            select(Candidate)
            .where(Candidate.election_id == election_id, Candidate.deleted_at.is_(None))
            .order_by(Candidate.display_order)
        )
        return list(self.db.scalars(stmt).all())

    def list_for_house(
        self,
        election_id: str,
        *,
        house_id: str | None = None,
        position_id: str | None = None,
    ) -> list[Candidate]:
        stmt = select(Candidate).where(
            Candidate.election_id == election_id,
            Candidate.deleted_at.is_(None),
            Candidate.house_id.is_not(None),
        )
        if house_id is not None:
            stmt = stmt.where(Candidate.house_id == house_id)
        if position_id is not None:
            stmt = stmt.where(Candidate.position_id == position_id)
        stmt = stmt.order_by(Candidate.display_order)
        return list(self.db.scalars(stmt).all())

    def list_by_status(self, status: CandidateStatus) -> list[Candidate]:
        return self.list_by_field("status", status)

    def search_by_name(self, name: str, *, election_id: str | None = None) -> list[Candidate]:
        pattern = f"%{name}%"
        stmt = select(Candidate).where(
            Candidate.candidate_name.ilike(pattern),
            Candidate.deleted_at.is_(None),
        )
        if election_id is not None:
            stmt = stmt.where(Candidate.election_id == election_id)
        stmt = stmt.order_by(Candidate.display_order)
        return list(self.db.scalars(stmt).all())

    def get_duplicate_name(
        self,
        position_id: str,
        candidate_name: str,
        *,
        house_id: str | None = None,
        exclude_id: str | None = None,
    ) -> Candidate | None:
        stmt = select(Candidate).where(
            Candidate.position_id == position_id,
            func.lower(Candidate.candidate_name) == candidate_name.strip().lower(),
            Candidate.deleted_at.is_(None),
        )
        if house_id is None:
            stmt = stmt.where(Candidate.house_id.is_(None))
        else:
            stmt = stmt.where(Candidate.house_id == house_id)
        if exclude_id is not None:
            stmt = stmt.where(Candidate.id != exclude_id)
        return self.db.scalar(stmt)

    def list_for_election_type(self, election_id: str, election_type: ElectionType) -> list[Candidate]:
        stmt = (
            select(Candidate)
            .join(Position, Candidate.position_id == Position.id)
            .where(
                Candidate.election_id == election_id,
                Position.election_type == election_type,
                Candidate.deleted_at.is_(None),
                Position.deleted_at.is_(None),
            )
            .order_by(Candidate.display_order)
        )
        return list(self.db.scalars(stmt).all())


class CandidateImageRepository(BaseRepository[CandidateImage]):
    """Data access for candidate image metadata."""

    model = CandidateImage
