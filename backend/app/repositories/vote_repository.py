"""Vote repository."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.models.sync import Vote
from app.repositories.base import BaseRepository


class VoteRepository(BaseRepository[Vote]):
    """Data access for synchronized vote records."""

    model = Vote

    def get_by_vote_uuid(self, vote_uuid: str) -> Vote | None:
        return self.get_by_field("vote_uuid", vote_uuid)

    def exists_by_vote_uuid(self, vote_uuid: str) -> bool:
        return self.get_by_vote_uuid(vote_uuid) is not None

    def list_for_election(self, election_id: str) -> list[Vote]:
        return self.list_by_field("election_id", election_id)

    def list_for_node(self, node_id: str) -> list[Vote]:
        return self.list_by_field("node_id", node_id)

    def count_all(self) -> int:
        stmt = select(func.count()).select_from(Vote)
        return int(self.db.scalar(stmt) or 0)

    def count_for_election(self, election_id: str) -> int:
        stmt = select(func.count()).select_from(Vote).where(Vote.election_id == election_id)
        return int(self.db.scalar(stmt) or 0)

    def count_for_node(self, node_id: str) -> int:
        stmt = select(func.count()).select_from(Vote).where(Vote.node_id == node_id)
        return int(self.db.scalar(stmt) or 0)

    def get_latest_sync_time(self) -> datetime | None:
        return self.db.scalar(select(func.max(Vote.synced_at)))

    def count_by_candidate(self, election_id: str) -> list[tuple[str, str, int]]:
        stmt = (
            select(Vote.candidate_id, Vote.position_id, func.count())
            .where(Vote.election_id == election_id)
            .group_by(Vote.candidate_id, Vote.position_id)
        )
        return [(row[0], row[1], int(row[2])) for row in self.db.execute(stmt).all()]

    def count_by_house(self, election_id: str) -> list[tuple[str, int]]:
        stmt = (
            select(Vote.house_id, func.count())
            .where(Vote.election_id == election_id, Vote.house_id.is_not(None))
            .group_by(Vote.house_id)
        )
        return [(row[0], int(row[1])) for row in self.db.execute(stmt).all()]

    def count_by_node(self, election_id: str) -> list[tuple[str, int]]:
        stmt = (
            select(Vote.node_id, func.count())
            .where(Vote.election_id == election_id)
            .group_by(Vote.node_id)
        )
        return [(row[0], int(row[1])) for row in self.db.execute(stmt).all()]

    def count_votes_per_minute(
        self,
        *,
        minutes: int = 30,
        election_id: str | None = None,
    ) -> list[tuple[datetime, int]]:
        cutoff = utc_now() - timedelta(minutes=minutes)
        conditions = [Vote.synced_at >= cutoff]
        if election_id is not None:
            conditions.append(Vote.election_id == election_id)
        stmt = (
            select(
                func.date_format(Vote.synced_at, "%Y-%m-%d %H:%i:00"),
                func.count(),
            )
            .where(*conditions)
            .group_by(func.date_format(Vote.synced_at, "%Y-%m-%d %H:%i:00"))
            .order_by(func.date_format(Vote.synced_at, "%Y-%m-%d %H:%i:00"))
        )
        rows = self.db.execute(stmt).all()
        parsed: list[tuple[datetime, int]] = []
        for minute_label, count in rows:
            try:
                minute_dt = datetime.strptime(str(minute_label), "%Y-%m-%d %H:%i:00").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                continue
            parsed.append((minute_dt, int(count)))
        return parsed

    def count_votes_per_hour(
        self,
        *,
        hours: int = 24,
        election_id: str | None = None,
    ) -> list[tuple[datetime, int]]:
        cutoff = utc_now() - timedelta(hours=hours)
        conditions = [Vote.synced_at >= cutoff]
        if election_id is not None:
            conditions.append(Vote.election_id == election_id)
        stmt = (
            select(
                func.date_format(Vote.synced_at, "%Y-%m-%d %H:00:00"),
                func.count(),
            )
            .where(*conditions)
            .group_by(func.date_format(Vote.synced_at, "%Y-%m-%d %H:00:00"))
            .order_by(func.date_format(Vote.synced_at, "%Y-%m-%d %H:00:00"))
        )
        rows = self.db.execute(stmt).all()
        parsed: list[tuple[datetime, int]] = []
        for hour_label, count in rows:
            try:
                hour_dt = datetime.strptime(str(hour_label), "%Y-%m-%d %H:00:00").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                continue
            parsed.append((hour_dt, int(count)))
        return parsed

    def get_node_vote_window(
        self,
        election_id: str,
        node_id: str,
    ) -> tuple[datetime | None, datetime | None]:
        stmt = select(func.min(Vote.voted_at), func.max(Vote.voted_at)).where(
            Vote.election_id == election_id,
            Vote.node_id == node_id,
        )
        row = self.db.execute(stmt).one()
        return row[0], row[1]
