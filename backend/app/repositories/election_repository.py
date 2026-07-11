"""Election repository."""

from sqlalchemy.orm import Session

from app.models.election import Election
from app.repositories.base import BaseRepository


class ElectionRepository(BaseRepository[Election]):
    """Data access for election records."""

    model = Election

    def __init__(self, db: Session) -> None:
        super().__init__(db)
