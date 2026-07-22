"""Analytics service tests."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from election_platform.enums.election import ElectionStatus, ElectionType

from app.schemas.report import (
    CandidateReportRow,
    HouseResultRow,
    NodeStatisticRow,
    PositionResultRow,
    ReportDataSnapshot,
    VoteSummary,
)
from app.services.analytics_service import AnalyticsService


def _election():
    election = MagicMock()
    election.id = "election-1"
    election.election_name = "Student Council 2026"
    election.status = ElectionStatus.LIVE
    return election


def _report_snapshot() -> ReportDataSnapshot:
    generated_at = datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)
    summary = VoteSummary(
        election_id="election-1",
        election_name="Student Council 2026",
        academic_year="2025-26",
        election_status=ElectionStatus.LIVE.value,
        total_votes=100,
        regular_votes=70,
        house_votes=30,
        position_count=2,
        candidate_count=3,
        generated_at=generated_at,
        generated_by="analytics",
        school_name="VNPS",
    )
    regular_candidate = CandidateReportRow(
        candidate_id="cand-1",
        candidate_name="Alice",
        position_id="pos-1",
        position_name="School Pupil Leader",
        election_type=ElectionType.REGULAR.value,
        vote_count=45,
        percentage=64.3,
        is_winner=True,
        rank=1,
    )
    regular_candidate_2 = CandidateReportRow(
        candidate_id="cand-2",
        candidate_name="Bob",
        position_id="pos-1",
        position_name="School Pupil Leader",
        election_type=ElectionType.REGULAR.value,
        vote_count=25,
        percentage=35.7,
        is_winner=False,
        rank=2,
    )
    house_candidate = CandidateReportRow(
        candidate_id="cand-3",
        candidate_name="Carol",
        position_id="pos-2",
        position_name="House Captain",
        election_type=ElectionType.HOUSE.value,
        house_name="Pallava",
        vote_count=30,
        percentage=100.0,
        is_winner=True,
        rank=1,
    )
    regular_position = PositionResultRow(
        position_id="pos-1",
        position_name="School Pupil Leader",
        election_type=ElectionType.REGULAR.value,
        total_votes=70,
        winner_count=1,
        candidates=[regular_candidate, regular_candidate_2],
    )
    house_position = PositionResultRow(
        position_id="pos-2",
        position_name="House Captain",
        election_type=ElectionType.HOUSE.value,
        total_votes=30,
        winner_count=1,
        candidates=[house_candidate],
    )
    return ReportDataSnapshot(
        summary=summary,
        final_results=[regular_position, house_position],
        regular_results=[regular_position],
        house_results=[
            HouseResultRow(
                house_id="house-1",
                house_name="Pallava",
                vote_count=30,
                percentage=30.0,
                positions=[house_position],
            )
        ],
        candidate_reports=[regular_candidate, regular_candidate_2, house_candidate],
        node_statistics=[
            NodeStatisticRow(
                node_id="node-1",
                node_name="Regular-01",
                election_type=ElectionType.REGULAR.value,
                vote_count=70,
            )
        ],
    )


def _build_service() -> AnalyticsService:
    vote_repository = MagicMock()
    election_repository = MagicMock()
    node_repository = MagicMock()
    heartbeat_repository = MagicMock()
    vote_queue_repository = MagicMock()
    candidate_repository = MagicMock()
    position_repository = MagicMock()
    house_repository = MagicMock()
    settings_repository = MagicMock()
    theme_repository = MagicMock()
    node_service = MagicMock()

    election_repository.get_by_id.return_value = _election()
    election_repository.list_by_status.return_value = [_election()]
    node_repository.list_all_ordered.return_value = []
    house_repository.list_all_ordered.return_value = []
    vote_repository.count_for_election.return_value = 100
    vote_repository.count_by_node.return_value = [("node-1", 70)]
    vote_repository.count_votes_per_minute.return_value = []
    vote_repository.count_votes_per_hour.return_value = []
    vote_repository.get_node_vote_window.return_value = (None, None)
    vote_queue_repository.list_by_status.return_value = []

    service = AnalyticsService(
        vote_repository=vote_repository,
        election_repository=election_repository,
        node_repository=node_repository,
        heartbeat_repository=heartbeat_repository,
        vote_queue_repository=vote_queue_repository,
        candidate_repository=candidate_repository,
        position_repository=position_repository,
        house_repository=house_repository,
        settings_repository=settings_repository,
        theme_repository=theme_repository,
        node_service=node_service,
    )
    service.data_collector = MagicMock()
    service.data_collector.collect.return_value = _report_snapshot()
    return service


def test_get_regular_analytics_includes_rankings() -> None:
    service = _build_service()
    snapshot = service.get_regular_analytics("election-1")

    assert snapshot.election_id == "election-1"
    assert len(snapshot.positions) == 1
    assert snapshot.positions[0].candidates[0].rank == 1
    assert snapshot.positions[0].candidates[0].is_winner is True
    assert len(snapshot.leading_candidates) == 1
    assert snapshot.leading_candidates[0].candidate_name == "Alice"


def test_get_house_analytics_returns_house_breakdown() -> None:
    service = _build_service()
    snapshot = service.get_house_analytics("election-1")

    assert snapshot.total_votes == 30
    assert len(snapshot.house_results) == 1
    assert snapshot.house_results[0].house_name == "Pallava"


def test_get_analytics_overview_aggregates_sections() -> None:
    service = _build_service()
    snapshot = service.get_analytics_overview("election-1")

    assert snapshot.summary.total_votes == 100
    assert snapshot.summary.regular_votes == 70
    assert snapshot.summary.house_votes == 30
    assert len(snapshot.regular_positions) == 1
    assert len(snapshot.house_results) == 1
    assert len(snapshot.leading_candidates) == 2


def test_turnout_uses_eligible_voter_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.settings import settings

    monkeypatch.setattr(settings, "analytics_eligible_voters", 100)
    service = _build_service()
    snapshot = service.get_regular_analytics("election-1")

    assert snapshot.turnout.estimated_participants == 70
    assert snapshot.turnout.turnout_percentage == 70.0


def test_get_live_results_includes_rank_and_winner() -> None:
    service = _build_service()
    snapshot = service.get_live_results("election-1")

    assert snapshot.total_votes == 100
    assert snapshot.positions[0].candidates[0].rank == 1
    assert snapshot.positions[0].candidates[0].is_winner is True
