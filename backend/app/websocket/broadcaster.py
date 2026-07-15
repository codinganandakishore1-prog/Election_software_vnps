"""WebSocket broadcast helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from election_platform.schemas.websocket import WSChannel, WSMessageType

from app.dependencies.container import Container
from app.schemas.notification import NotificationResponse
from app.websocket.manager import manager


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


async def send_dashboard_snapshot(container: Container) -> int:
    snapshot = container.analytics_service.get_dashboard_snapshot(
        connected_clients=manager.connected_count_for(WSChannel.DASHBOARD),
    )
    return await manager.broadcast_to_channel(
        WSChannel.DASHBOARD,
        {
            "type": WSMessageType.DASHBOARD_SNAPSHOT.value,
            "data": snapshot.model_dump(mode="json"),
        },
    )


async def send_live_results_snapshot(container: Container) -> int:
    snapshot = container.analytics_service.get_live_results()
    return await manager.broadcast_to_channel(
        WSChannel.LIVE,
        {
            "type": WSMessageType.LIVE_RESULTS_UPDATE.value,
            "data": snapshot.model_dump(mode="json"),
        },
    )


async def broadcast_vote_synced(
    container: Container,
    *,
    node_id: str,
    accepted_count: int,
    vote_uuids: list[str],
) -> None:
    node = container.node_repository.get_by_id(node_id)
    node_name = node.node_name if node else node_id

    vote_details: list[dict] = []
    for vote_uuid in vote_uuids:
        vote = container.vote_repository.get_by_vote_uuid(vote_uuid)
        if vote is None:
            continue
        candidate = container.candidate_repository.get_by_id(vote.candidate_id)
        position = container.position_repository.get_by_id(vote.position_id)
        vote_details.append(
            {
                "vote_uuid": vote.vote_uuid,
                "election_id": vote.election_id,
                "position_id": vote.position_id,
                "position_name": position.position_name if position else "",
                "candidate_id": vote.candidate_id,
                "candidate_name": candidate.candidate_name if candidate else "",
            }
        )

    dashboard_snapshot = container.analytics_service.get_dashboard_snapshot(
        connected_clients=manager.connected_count_for(WSChannel.DASHBOARD),
    )
    live_results = container.analytics_service.get_live_results()

    await manager.broadcast_to_channel(
        WSChannel.DASHBOARD,
        {
            "type": WSMessageType.VOTE_SYNCED.value,
            "node_id": node_id,
            "node_name": node_name,
            "accepted_count": accepted_count,
            "vote_uuids": vote_uuids,
            "votes": vote_details,
            "total_votes": dashboard_snapshot.total_votes,
            "last_vote_time": _iso(dashboard_snapshot.last_vote_time),
        },
    )
    await manager.broadcast_to_channel(
        WSChannel.DASHBOARD,
        {
            "type": WSMessageType.VOTE_COUNTS.value,
            "data": dashboard_snapshot.model_dump(mode="json"),
        },
    )
    await manager.broadcast_to_channel(
        WSChannel.LIVE,
        {
            "type": WSMessageType.LIVE_RESULTS_UPDATE.value,
            "data": live_results.model_dump(mode="json"),
        },
    )


async def broadcast_heartbeat(
    container: Container,
    *,
    node_id: str,
    node_name: str,
    status: str,
    queue_size: int,
    sync_status: str | None,
    config_version: int,
    last_vote_time: datetime | None,
    last_heartbeat: datetime | None,
) -> None:
    node_votes = container.vote_repository.count_for_node(node_id)

    await manager.broadcast_to_channel(
        WSChannel.DASHBOARD,
        {
            "type": WSMessageType.HEARTBEAT_RECEIVED.value,
            "node_id": node_id,
            "node_name": node_name,
            "status": status,
            "queue_size": queue_size,
            "sync_status": sync_status,
            "config_version": config_version,
            "last_vote_time": _iso(last_vote_time),
            "last_heartbeat": _iso(last_heartbeat),
            "votes": node_votes,
        },
    )
    await manager.broadcast_to_channel(
        WSChannel.DASHBOARD,
        {
            "type": WSMessageType.NODE_STATUS.value,
            "node_id": node_id,
            "node_name": node_name,
            "status": status,
            "queue_size": queue_size,
            "sync_status": sync_status,
            "votes": node_votes,
            "last_heartbeat": _iso(last_heartbeat),
        },
    )


async def broadcast_sync_status(
    container: Container,
    *,
    node_id: str,
    node_name: str,
    sync_status: str,
    queue_size: int,
    failed_count: int = 0,
) -> None:
    snapshot = container.analytics_service.get_dashboard_snapshot(
        connected_clients=manager.connected_count_for(WSChannel.DASHBOARD),
    )
    await manager.broadcast_to_channel(
        WSChannel.DASHBOARD,
        {
            "type": WSMessageType.SYNC_STATUS.value,
            "node_id": node_id,
            "node_name": node_name,
            "sync_status": sync_status,
            "queue_size": queue_size,
            "failed_count": failed_count,
            "pending_queue": snapshot.pending_queue,
            "sync_errors": snapshot.sync_errors,
        },
    )

    if failed_count > 0:
        await container.notification_service.create_and_broadcast(
            title="Synchronization issue",
            message=f"{failed_count} vote(s) failed to sync from {node_name}.",
            notification_type="Synchronization Failed",
        )


async def broadcast_notification(notification: NotificationResponse) -> int:
    return await manager.broadcast_to_channel(
        WSChannel.DASHBOARD,
        {
            "type": WSMessageType.NOTIFICATION.value,
            "data": notification.model_dump(mode="json"),
        },
    )


async def broadcast_election_status(
    *,
    election_id: str,
    election_name: str,
    status: str,
) -> None:
    message = {
        "type": WSMessageType.ELECTION_STATUS.value,
        "election_id": election_id,
        "election_name": election_name,
        "status": status,
    }
    await manager.broadcast(message, channels=[WSChannel.DASHBOARD, WSChannel.LIVE])
