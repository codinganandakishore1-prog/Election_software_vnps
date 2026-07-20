"""Vote repository."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.sql.elements import ColumnElement

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

    def _time_bucket(self, column: ColumnElement, *, granularity: str) -> ColumnElement:
        """Dialect-safe minute/hour truncation for SQLite and MySQL."""
        bind = self.db.get_bind()
        dialect = bind.dialect.name if bind is not None else "sqlite"
        if dialect == "sqlite":
            fmt = "%Y-%m-%d %H:%M:00" if granularity == "minute" else "%Y-%m-%d %H:00:00"
            return func.strftime(fmt, column)
        # MySQL / MariaDB
        fmt = "%Y-%m-%d %H:%i:00" if granularity == "minute" else "%Y-%m-%d %H:00:00"
        return func.date_format(column, fmt)

    @staticmethod
    def _parse_bucket_label(label: object, *, granularity: str) -> datetime | None:
        pattern = "%Y-%m-%d %H:%M:00" if granularity == "minute" else "%Y-%m-%d %H:00:00"
        try:
            return datetime.strptime(str(label), pattern).replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    def count_votes_per_minute(
        self,
        *,
        minutes: int = 30,
        election_id: str | None = None,
    ) -> list[tuple[datetime, int]]:
        return self._count_votes_by_bucket(
            granularity="minute",
            cutoff=utc_now() - timedelta(minutes=minutes),
            election_id=election_id,
        )

    def count_votes_per_hour(
        self,
        *,
        hours: int = 24,
        election_id: str | None = None,
    ) -> list[tuple[datetime, int]]:
        return self._count_votes_by_bucket(
            granularity="hour",
            cutoff=utc_now() - timedelta(hours=hours),
            election_id=election_id,
        )

    def _count_votes_by_bucket(
        self,
        *,
        granularity: str,
        cutoff: datetime,
        election_id: str | None,
    ) -> list[tuple[datetime, int]]:
        # Prefer synced_at; fall back to voted_at when sync timestamps are sparse.
        for column in (Vote.synced_at, Vote.voted_at):
            conditions = [column >= cutoff]
            if election_id is not None:
                conditions.append(Vote.election_id == election_id)
            bucket = self._time_bucket(column, granularity=granularity)
            stmt = (
                select(bucket, func.count())
                .where(*conditions)
                .group_by(bucket)
                .order_by(bucket)
            )
            parsed: list[tuple[datetime, int]] = []
            for label, count in self.db.execute(stmt).all():
                parsed_dt = self._parse_bucket_label(label, granularity=granularity)
                if parsed_dt is not None:
                    parsed.append((parsed_dt, int(count)))
            if parsed:
                return parsed
        return []

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
