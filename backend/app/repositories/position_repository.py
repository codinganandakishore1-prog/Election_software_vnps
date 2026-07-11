"""Position repository."""

from sqlalchemy.orm import Session

from app.models.position import Position
from app.repositories.base import BaseRepository


class PositionRepository(BaseRepository[Position]):
    """Data access for position records."""

    model = Position

    def __init__(self, db: Session) -> None:
        super().__init__(db)
