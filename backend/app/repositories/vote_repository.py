"""Vote repository."""

from sqlalchemy.orm import Session

from app.models.sync import Vote
from app.repositories.base import BaseRepository


class VoteRepository(BaseRepository[Vote]):
    """Data access for vote records."""

    model = Vote

    def __init__(self, db: Session) -> None:
        super().__init__(db)
