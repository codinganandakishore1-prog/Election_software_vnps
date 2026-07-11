"""User repository."""

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access for user records."""

    model = User

    def __init__(self, db: Session) -> None:
        super().__init__(db)
