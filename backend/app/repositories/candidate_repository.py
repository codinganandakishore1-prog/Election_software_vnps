"""Candidate repository."""

from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.repositories.base import BaseRepository


class CandidateRepository(BaseRepository[Candidate]):
    """Data access for candidate records."""

    model = Candidate

    def __init__(self, db: Session) -> None:
        super().__init__(db)
