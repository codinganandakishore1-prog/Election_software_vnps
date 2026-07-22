"""Analytics router."""

from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, Query

from app.dependencies.auth import CurrentUser
from app.dependencies.providers import ServiceContainer
from app.schemas.analytics import (
    AnalyticsOverviewSnapshot,
    DashboardSnapshot,
    HouseAnalyticsSnapshot,
    LiveResultsSnapshot,
    NodePerformanceSnapshot,
    RegularAnalyticsSnapshot,
    TimelineSnapshot,
)
from app.websocket.manager import manager
from election_platform.schemas.websocket import WSChannel

router = APIRouter()


@router.get("")
async def analytics_overview(
    current_user: CurrentUser,
    container: ServiceContainer,
    election_id: str | None = Query(default=None),
) -> APIResponse[AnalyticsOverviewSnapshot]:
    """Return the full analytics overview."""
    _ = current_user
    snapshot = container.analytics_service.get_analytics_overview(election_id=election_id)
    return APIResponse.ok(data=snapshot)


@router.get("/dashboard")
async def dashboard_analytics(
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[DashboardSnapshot]:
    """Return dashboard statistics."""
    _ = current_user
    snapshot = container.analytics_service.get_dashboard_snapshot(
        connected_clients=manager.connected_count_for(WSChannel.DASHBOARD),
    )
    return APIResponse.ok(data=snapshot)


@router.get("/live")
async def live_results_analytics(
    container: ServiceContainer,
    election_id: str | None = Query(default=None),
) -> APIResponse[LiveResultsSnapshot]:
    """Return live election results (public read)."""
    snapshot = container.analytics_service.get_live_results(election_id=election_id)
    return APIResponse.ok(data=snapshot)


@router.get("/regular")
async def regular_election_analytics(
    current_user: CurrentUser,
    container: ServiceContainer,
    election_id: str | None = Query(default=None),
) -> APIResponse[RegularAnalyticsSnapshot]:
    """Return regular election statistics with rankings."""
    _ = current_user
    snapshot = container.analytics_service.get_regular_analytics(election_id=election_id)
    return APIResponse.ok(data=snapshot)


@router.get("/houses")
async def house_election_analytics(
    current_user: CurrentUser,
    container: ServiceContainer,
    election_id: str | None = Query(default=None),
) -> APIResponse[HouseAnalyticsSnapshot]:
    """Return house election statistics."""
    _ = current_user
    snapshot = container.analytics_service.get_house_analytics(election_id=election_id)
    return APIResponse.ok(data=snapshot)


@router.get("/nodes")
async def node_performance_analytics(
    current_user: CurrentUser,
    container: ServiceContainer,
    election_id: str | None = Query(default=None),
) -> APIResponse[NodePerformanceSnapshot]:
    """Return node performance and contribution analytics."""
    _ = current_user
    snapshot = container.analytics_service.get_node_performance(election_id=election_id)
    return APIResponse.ok(data=snapshot)


@router.get("/timeline")
async def voting_timeline_analytics(
    current_user: CurrentUser,
    container: ServiceContainer,
    election_id: str | None = Query(default=None),
    interval: str = Query(default="minute", pattern="^(minute|hour)$"),
    window: int = Query(default=30, ge=5, le=168),
) -> APIResponse[TimelineSnapshot]:
    """Return voting activity timeline for charts."""
    _ = current_user
    snapshot = container.analytics_service.get_timeline(
        election_id=election_id,
        interval=interval,
        window=window,
    )
    return APIResponse.ok(data=snapshot)
