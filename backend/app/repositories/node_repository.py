"""Voting node repositories."""

from election_platform.enums.election import ElectionType
from election_platform.enums.sync import QueueStatus, SyncStatus
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.node import NodeDownload, NodeHeartbeat, NodeSession, VotingNode
from app.models.sync import PublishedConfiguration, SyncLog, VoteQueue
from app.repositories.base import BaseRepository


class NodeRepository(BaseRepository[VotingNode]):
    """Data access for voting node records."""

    model = VotingNode

    def get_by_name(self, node_name: str) -> VotingNode | None:
        return self.get_by_field("node_name", node_name)

    def list_active(self, *, limit: int | None = None, offset: int = 0) -> list[VotingNode]:
        return self.list_by_field("active", True, limit=limit, offset=offset)

    def list_all_ordered(self) -> list[VotingNode]:
        stmt = select(VotingNode).order_by(VotingNode.node_name)
        return list(self.db.scalars(stmt).all())

    def list_by_election_type(self, election_type: ElectionType) -> list[VotingNode]:
        stmt = (
            select(VotingNode)
            .where(VotingNode.election_type == election_type)
            .order_by(VotingNode.node_name)
        )
        return list(self.db.scalars(stmt).all())


class NodeHeartbeatRepository(BaseRepository[NodeHeartbeat]):
    """Data access for node heartbeat history."""

    model = NodeHeartbeat

    def get_latest_for_node(self, node_id: str) -> NodeHeartbeat | None:
        stmt = (
            select(NodeHeartbeat)
            .where(NodeHeartbeat.node_id == node_id)
            .order_by(NodeHeartbeat.heartbeat_time.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def list_by_sync_status(self, sync_status: SyncStatus) -> list[NodeHeartbeat]:
        return self.list_by_field("sync_status", sync_status)


class NodeSessionRepository(BaseRepository[NodeSession]):
    """Data access for node session records."""

    model = NodeSession

    def list_for_node(self, node_id: str) -> list[NodeSession]:
        return self.list_by_field("node_id", node_id)

    def get_active_session(self, session_id: str) -> NodeSession | None:
        from election_platform.enums.admin import SessionStatus

        return self.db.scalar(
            select(NodeSession).where(
                NodeSession.id == session_id,
                NodeSession.session_status == SessionStatus.ACTIVE,
            )
        )


class NodeDownloadRepository(BaseRepository[NodeDownload]):
    """Data access for configuration download records."""

    model = NodeDownload

    def list_for_node(self, node_id: str) -> list[NodeDownload]:
        return self.list_by_field("node_id", node_id)


class PublishedConfigurationRepository(BaseRepository[PublishedConfiguration]):
    """Data access for published configuration packages."""

    model = PublishedConfiguration

    def get_latest_for_election(self, election_id: str) -> PublishedConfiguration | None:
        stmt = (
            select(PublishedConfiguration)
            .where(PublishedConfiguration.election_id == election_id)
            .order_by(PublishedConfiguration.version.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def list_for_election(self, election_id: str) -> list[PublishedConfiguration]:
        stmt = (
            select(PublishedConfiguration)
            .where(PublishedConfiguration.election_id == election_id)
            .order_by(PublishedConfiguration.version.desc())
        )
        return list(self.db.scalars(stmt).all())


class VoteQueueRepository(BaseRepository[VoteQueue]):
    """Data access for website vote queue monitoring."""

    model = VoteQueue

    def get_by_vote_uuid(self, vote_uuid: str) -> VoteQueue | None:
        return self.get_by_field("vote_uuid", vote_uuid)

    def list_pending_for_node(self, node_id: str) -> list[VoteQueue]:
        stmt = select(VoteQueue).where(
            VoteQueue.node_id == node_id,
            VoteQueue.queue_status == QueueStatus.PENDING,
        )
        return list(self.db.scalars(stmt).all())

    def list_by_status(self, queue_status: QueueStatus) -> list[VoteQueue]:
        return self.list_by_field("queue_status", queue_status)


class SyncLogRepository(BaseRepository[SyncLog]):
    """Data access for synchronization logs."""

    model = SyncLog

    def list_for_node(self, node_id: str, *, limit: int | None = None) -> list[SyncLog]:
        stmt = (
            select(SyncLog)
            .where(SyncLog.node_id == node_id)
            .order_by(SyncLog.sync_start.desc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())
