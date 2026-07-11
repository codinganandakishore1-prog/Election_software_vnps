"""Local vote repository (placeholder)."""

from sqlalchemy.orm import Session

from desktop.app.models.local_vote import LocalVote


class LocalVoteRepository:
    """Data access for local vote records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, vote: LocalVote) -> LocalVote:
        self.db.add(vote)
        return vote
