"""Analytics service for dashboard and live results."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from election_platform.enums.election import ElectionStatus, ElectionType
from election_platform.enums.sync import QueueStatus

from app.config.settings import settings
from app.database.base import utc_now
from app.reports.data import ReportDataCollector
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.election_repository import ElectionRepository
from app.repositories.house_repository import HouseRepository
from app.repositories.node_repository import NodeHeartbeatRepository, NodeRepository, VoteQueueRepository
from app.repositories.position_repository import PositionRepository
from app.repositories.settings_repository import SettingsRepository, ThemeRepository
from app.repositories.vote_repository import VoteRepository
from app.schemas.analytics import (
    ActivityEntry,
    AnalyticsOverviewSnapshot,
    AnalyticsSummary,
    DashboardSnapshot,
    HouseAnalyticsSnapshot,
    LeadingCandidateEntry,
    LiveResultsSnapshot,
    NodeHealthEntry,
    NodePerformanceEntry,
    NodePerformanceSnapshot,
    PositionResults,
    RegularAnalyticsSnapshot,
    TimelineEntry,
    TimelineSnapshot,
    TurnoutStats,
    VoteCountEntry,
    VotesPerMinuteEntry,
)
from app.schemas.report import HouseResultRow, PositionResultRow
from app.services.base import BaseService
from app.services.node_service import NodeService


class AnalyticsService(BaseService):
    """Handles live statistics and dashboard analytics."""

    def __init__(
        self,
        vote_repository: VoteRepository,
        election_repository: ElectionRepository,
        node_repository: NodeRepository,
        heartbeat_repository: NodeHeartbeatRepository,
        vote_queue_repository: VoteQueueRepository,
        candidate_repository: CandidateRepository,
        position_repository: PositionRepository,
        house_repository: HouseRepository,
        settings_repository: SettingsRepository,
        theme_repository: ThemeRepository,
        node_service: NodeService,
    ) -> None:
        self.vote_repository = vote_repository
        self.election_repository = election_repository
        self.node_repository = node_repository
        self.heartbeat_repository = heartbeat_repository
        self.vote_queue_repository = vote_queue_repository
        self.candidate_repository = candidate_repository
        self.position_repository = position_repository
        self.house_repository = house_repository
        self.settings_repository = settings_repository
        self.theme_repository = theme_repository
        self.node_service = node_service
        self.data_collector = ReportDataCollector(
            election_repository=election_repository,
            position_repository=position_repository,
            candidate_repository=candidate_repository,
            house_repository=house_repository,
            node_repository=node_repository,
            vote_repository=vote_repository,
            settings_repository=settings_repository,
            theme_repository=theme_repository,
        )

    def get_dashboard_snapshot(self, *, connected_clients: int = 0) -> DashboardSnapshot:
        election = self._get_primary_election()
        election_id = election.id if election else None
        total_votes = (
            self.vote_repository.count_for_election(election_id)
            if election_id
            else self.vote_repository.count_all()
        )

        nodes = [node for node in self.node_repository.list_all_ordered() if node.active]
        node_rows: list[NodeHealthEntry] = []
        online_nodes = 0
        pending_queue = 0

        for node in nodes:
            health = self.node_service.get_node_health(node.id)
            if health.status == "Online":
                online_nodes += 1
            pending_queue += health.queue_size or 0
            node_rows.append(
                NodeHealthEntry(
                    node_id=node.id,
                    name=health.node_name,
                    status=health.status,
                    votes=self.vote_repository.count_for_node(node.id),
                    queue=health.queue_size or 0,
                    sync_status=health.sync_status,
                    last_heartbeat=health.last_heartbeat,
                )
            )

        sync_errors = len(self.vote_queue_repository.list_by_status(QueueStatus.FAILED))
        last_vote_time = self.vote_repository.get_latest_sync_time()

        return DashboardSnapshot(
            election_name=election.election_name if election else "No active election",
            election_status=election.status.value if election else "Draft",
            total_votes=total_votes,
            online_nodes=online_nodes,
            total_nodes=len(nodes),
            pending_queue=pending_queue,
            sync_errors=sync_errors,
            last_vote_time=last_vote_time,
            connected_clients=connected_clients,
            nodes=node_rows,
            activity=self._build_activity(node_rows, last_vote_time),
            votes_per_minute=self._build_votes_per_minute(election_id),
        )

    def get_live_results(self, election_id: str | None = None) -> LiveResultsSnapshot:
        snapshot = self._build_results_snapshot(election_id=election_id)
        if snapshot is None:
            return LiveResultsSnapshot()
        return LiveResultsSnapshot(
            election_id=snapshot.election_id,
            election_name=snapshot.election_name,
            election_status=snapshot.election_status,
            total_votes=snapshot.total_votes,
            updated_at=snapshot.updated_at,
            positions=snapshot.positions,
        )

    def get_analytics_overview(self, election_id: str | None = None) -> AnalyticsOverviewSnapshot:
        election = self._resolve_election(election_id)
        if election is None:
            return AnalyticsOverviewSnapshot(summary=AnalyticsSummary())

        report_data = self.data_collector.collect(election.id, generated_by="analytics")
        summary = self._build_summary(report_data)
        node_statistics = self._build_node_performance(election.id, report_data.summary.total_votes)
        leading_candidates = self._build_leading_candidates(report_data.final_results)

        return AnalyticsOverviewSnapshot(
            summary=summary,
            regular_positions=report_data.regular_results,
            house_results=report_data.house_results,
            node_statistics=node_statistics,
            leading_candidates=leading_candidates,
            votes_per_minute=self._build_votes_per_minute(election.id),
            timeline=self._build_timeline(election_id=election.id, interval="hour", window=48),
        )

    def get_regular_analytics(self, election_id: str | None = None) -> RegularAnalyticsSnapshot:
        election = self._resolve_election(election_id)
        if election is None:
            return RegularAnalyticsSnapshot()

        report_data = self.data_collector.collect(election.id, generated_by="analytics")
        turnout = self._build_turnout(
            report_data.regular_results,
            self._house_position_results(report_data),
        )

        return RegularAnalyticsSnapshot(
            election_id=election.id,
            election_name=election.election_name,
            election_status=election.status.value,
            total_votes=sum(position.total_votes for position in report_data.regular_results),
            turnout=turnout,
            positions=report_data.regular_results,
            leading_candidates=self._build_leading_candidates(report_data.regular_results),
            updated_at=utc_now(),
        )

    def get_house_analytics(self, election_id: str | None = None) -> HouseAnalyticsSnapshot:
        election = self._resolve_election(election_id)
        if election is None:
            return HouseAnalyticsSnapshot()

        report_data = self.data_collector.collect(election.id, generated_by="analytics")

        return HouseAnalyticsSnapshot(
            election_id=election.id,
            election_name=election.election_name,
            election_status=election.status.value,
            total_votes=report_data.summary.house_votes,
            house_results=report_data.house_results,
            updated_at=utc_now(),
        )

    def get_node_performance(self, election_id: str | None = None) -> NodePerformanceSnapshot:
        election = self._resolve_election(election_id)
        if election is None:
            return NodePerformanceSnapshot()

        total_votes = self.vote_repository.count_for_election(election.id)
        nodes = self._build_node_performance(election.id, total_votes)

        return NodePerformanceSnapshot(
            election_id=election.id,
            election_name=election.election_name,
            total_votes=total_votes,
            nodes=nodes,
            updated_at=utc_now(),
        )

    def get_timeline(
        self,
        *,
        election_id: str | None = None,
        interval: str = "minute",
        window: int = 30,
    ) -> TimelineSnapshot:
        election = self._resolve_election(election_id)
        if election is None:
            return TimelineSnapshot(interval=interval)

        points = self._build_timeline(
            election_id=election.id,
            interval=interval,
            window=window,
        )
        return TimelineSnapshot(
            election_id=election.id,
            election_name=election.election_name,
            interval=interval,
            points=points,
            updated_at=utc_now(),
        )

    def _build_results_snapshot(
        self,
        *,
        election_id: str | None = None,
        election_type: ElectionType | None = None,
    ) -> LiveResultsSnapshot | None:
        election = self._resolve_election(election_id)
        if election is None:
            return None

        report_data = self.data_collector.collect(election.id, generated_by="analytics")
        positions = report_data.final_results
        if election_type is not None:
            positions = [position for position in positions if position.election_type == election_type.value]

        converted_positions = [self._to_position_results(position) for position in positions]
        return LiveResultsSnapshot(
            election_id=election.id,
            election_name=election.election_name,
            election_status=election.status.value,
            total_votes=sum(position.total_votes for position in converted_positions),
            updated_at=utc_now(),
            positions=converted_positions,
        )

    def _build_summary(self, report_data) -> AnalyticsSummary:
        summary = report_data.summary
        nodes = [node for node in self.node_repository.list_all_ordered() if node.active]
        online_nodes = sum(
            1 for node in nodes if self.node_service.get_node_health(node.id).status == "Online"
        )

        return AnalyticsSummary(
            election_id=summary.election_id,
            election_name=summary.election_name,
            election_status=summary.election_status,
            total_votes=summary.total_votes,
            regular_votes=summary.regular_votes,
            house_votes=summary.house_votes,
            online_nodes=online_nodes,
            total_nodes=len(nodes),
            position_count=summary.position_count,
            candidate_count=summary.candidate_count,
            turnout=self._build_turnout(
                report_data.regular_results,
                self._house_position_results(report_data),
            ),
            updated_at=utc_now(),
        )

    def _house_position_results(self, report_data) -> list[PositionResultRow]:
        return [
            position
            for position in report_data.final_results
            if position.election_type == ElectionType.HOUSE.value
        ]

    def _build_turnout(
        self,
        regular_positions: list[PositionResultRow],
        house_positions: list[PositionResultRow],
    ) -> TurnoutStats:
        regular_participants = max(
            (position.total_votes for position in regular_positions),
            default=0,
        )
        house_participants = max(
            (position.total_votes for position in house_positions),
            default=0,
        )
        estimated_participants = max(regular_participants, house_participants)
        eligible_voters = settings.analytics_eligible_voters
        turnout_percentage = None
        if eligible_voters and eligible_voters > 0 and estimated_participants > 0:
            turnout_percentage = round(min((estimated_participants / eligible_voters) * 100, 100.0), 1)

        return TurnoutStats(
            eligible_voters=eligible_voters,
            estimated_participants=estimated_participants,
            turnout_percentage=turnout_percentage,
            regular_participants=regular_participants,
            house_participants=house_participants,
        )

    def _build_leading_candidates(
        self,
        positions: list[PositionResultRow],
    ) -> list[LeadingCandidateEntry]:
        leaders: list[LeadingCandidateEntry] = []
        for position in positions:
            if not position.candidates:
                continue
            leader = position.candidates[0]
            runner_up_votes = position.candidates[1].vote_count if len(position.candidates) > 1 else 0
            margin = round(leader.percentage - ((runner_up_votes / position.total_votes) * 100 if position.total_votes else 0.0), 1)
            leaders.append(
                LeadingCandidateEntry(
                    position_id=position.position_id,
                    position_name=position.position_name,
                    candidate_id=leader.candidate_id,
                    candidate_name=leader.candidate_name,
                    vote_count=leader.vote_count,
                    percentage=leader.percentage,
                    margin=margin,
                )
            )
        return leaders

    def _build_node_performance(self, election_id: str, total_votes: int) -> list[NodePerformanceEntry]:
        nodes = self.node_repository.list_all_ordered()
        houses = {house.id: house.house_name for house in self.house_repository.list_all_ordered()}
        node_vote_map = {
            node_id: count for node_id, count in self.vote_repository.count_by_node(election_id)
        }
        performance_rows: list[NodePerformanceEntry] = []

        for node in nodes:
            health = self.node_service.get_node_health(node.id)
            vote_count = node_vote_map.get(node.id, 0)
            first_vote, last_vote = self.vote_repository.get_node_vote_window(election_id, node.id)
            votes_per_hour = self._compute_votes_per_hour(vote_count, first_vote, last_vote)

            performance_rows.append(
                NodePerformanceEntry(
                    node_id=node.id,
                    node_name=node.node_name,
                    election_type=node.election_type.value,
                    house_name=houses.get(node.house_id) if node.house_id else None,
                    vote_count=vote_count,
                    contribution_percentage=round((vote_count / total_votes) * 100, 1) if total_votes else 0.0,
                    status=health.status,
                    sync_status=health.sync_status,
                    queue_size=health.queue_size or 0,
                    last_heartbeat=health.last_heartbeat,
                    votes_per_hour=votes_per_hour,
                )
            )

        return sorted(performance_rows, key=lambda item: item.vote_count, reverse=True)

    def _build_timeline(
        self,
        *,
        election_id: str,
        interval: str,
        window: int,
    ) -> list[TimelineEntry]:
        if interval == "hour":
            rows = self.vote_repository.count_votes_per_hour(hours=window, election_id=election_id)
            return [
                TimelineEntry(label=hour_dt.astimezone(timezone.utc).strftime("%H:00"), count=count)
                for hour_dt, count in rows
            ]

        rows = self.vote_repository.count_votes_per_minute(minutes=window, election_id=election_id)
        return [
            TimelineEntry(label=minute_dt.astimezone(timezone.utc).strftime("%H:%M"), count=count)
            for minute_dt, count in rows
        ]

    def _build_votes_per_minute(self, election_id: str | None = None) -> list[VotesPerMinuteEntry]:
        rows = self.vote_repository.count_votes_per_minute(minutes=30, election_id=election_id)
        return [
            VotesPerMinuteEntry(
                minute=minute_dt.astimezone(timezone.utc).strftime("%H:%M"),
                count=count,
            )
            for minute_dt, count in rows
        ]

    def _resolve_election(self, election_id: str | None):
        if election_id:
            return self.election_repository.get_by_id(election_id)
        return self._get_primary_election()

    def _get_primary_election(self):
        live = self.election_repository.list_by_status(ElectionStatus.LIVE)
        if live:
            return live[0]
        published = self.election_repository.list_by_status(ElectionStatus.PUBLISHED)
        if published:
            return published[0]
        elections = self.election_repository.list_filtered(active_only=True, limit=1)
        return elections[0] if elections else None

    @staticmethod
    def _to_position_results(position: PositionResultRow) -> PositionResults:
        return PositionResults(
            position_id=position.position_id,
            position_name=position.position_name,
            election_type=position.election_type,
            total_votes=position.total_votes,
            winner_count=position.winner_count,
            candidates=[
                VoteCountEntry(
                    candidate_id=candidate.candidate_id,
                    candidate_name=candidate.candidate_name,
                    position_id=candidate.position_id,
                    position_name=candidate.position_name,
                    vote_count=candidate.vote_count,
                    percentage=candidate.percentage,
                    rank=candidate.rank,
                    is_winner=candidate.is_winner,
                )
                for candidate in position.candidates
            ],
        )

    @staticmethod
    def _compute_votes_per_hour(
        vote_count: int,
        first_vote: datetime | None,
        last_vote: datetime | None,
    ) -> float | None:
        if vote_count == 0 or first_vote is None or last_vote is None:
            return None
        if first_vote.tzinfo is None:
            first_vote = first_vote.replace(tzinfo=timezone.utc)
        if last_vote.tzinfo is None:
            last_vote = last_vote.replace(tzinfo=timezone.utc)
        elapsed_hours = max((last_vote - first_vote).total_seconds() / 3600, 1 / 60)
        return round(vote_count / elapsed_hours, 1)

    def _build_activity(
        self,
        nodes: list[NodeHealthEntry],
        last_vote_time: datetime | None,
    ) -> list[ActivityEntry]:
        activity: list[ActivityEntry] = []

        if last_vote_time is not None:
            activity.append(
                ActivityEntry(
                    time=self._format_time(last_vote_time),
                    message=f"Last vote synced at {self._format_time(last_vote_time)}",
                    event_type="vote",
                )
            )

        for node in nodes[:5]:
            if node.last_heartbeat is not None:
                activity.append(
                    ActivityEntry(
                        time=self._format_time(node.last_heartbeat),
                        message=f"{node.name} heartbeat — {node.status}",
                        event_type="heartbeat",
                    )
                )

        offline_nodes = [node for node in nodes if node.status == "Offline"]
        for node in offline_nodes[:3]:
            activity.append(
                ActivityEntry(
                    time=self._format_relative(node.last_heartbeat),
                    message=f"{node.name} is offline",
                    event_type="warning",
                )
            )

        return activity[:8]

    @staticmethod
    def _format_time(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).strftime("%H:%M")

    def _format_relative(self, value: datetime | None) -> str:
        if value is None:
            return "—"
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        delta = utc_now() - value
        if delta < timedelta(minutes=1):
            return "just now"
        if delta < timedelta(hours=1):
            return f"{int(delta.total_seconds() // 60)} min ago"
        return self._format_time(value)
