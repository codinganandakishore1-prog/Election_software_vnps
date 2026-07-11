"""Voting node repository."""

from sqlalchemy.orm import Session

from app.models.node import VotingNode
from app.repositories.base import BaseRepository


class NodeRepository(BaseRepository[VotingNode]):
    """Data access for voting node records."""

    model = VotingNode

    def __init__(self, db: Session) -> None:
        super().__init__(db)
