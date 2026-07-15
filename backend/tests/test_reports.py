"""Report generation tests."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from election_platform.enums.admin import ReportType
from election_platform.enums.election import ElectionStatus, ElectionType

from app.exceptions.base import NotFoundError
from app.reports.csv_generator import CsvReportGenerator
from app.reports.data import ReportDataCollector
from app.reports.excel_generator import ExcelReportGenerator
from app.reports.pdf_generator import PdfReportGenerator
from app.schemas.report import (
    CandidateReportRow,
    HouseResultRow,
    NodeStatisticRow,
    PositionResultRow,
    ReportDataSnapshot,
    VoteSummary,
)
from app.services.report_service import ReportService


def _sample_snapshot() -> ReportDataSnapshot:
    generated_at = datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)
    summary = VoteSummary(
        election_id="election-1",
        election_name="Student Council 2026",
        academic_year="2025-26",
        election_status=ElectionStatus.COMPLETED.value,
        total_votes=100,
        regular_votes=70,
        house_votes=30,
        position_count=2,
        candidate_count=3,
        generated_at=generated_at,
        generated_by="Admin User",
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
    return ReportDataSnapshot(
        summary=summary,
        final_results=[
            PositionResultRow(
                position_id="pos-1",
                position_name="School Pupil Leader",
                election_type=ElectionType.REGULAR.value,
                total_votes=70,
                winner_count=1,
                candidates=[regular_candidate, regular_candidate_2],
            ),
            PositionResultRow(
                position_id="pos-2",
                position_name="House Captain",
                election_type=ElectionType.HOUSE.value,
                total_votes=30,
                winner_count=1,
                candidates=[house_candidate],
            ),
        ],
        regular_results=[
            PositionResultRow(
                position_id="pos-1",
                position_name="School Pupil Leader",
                election_type=ElectionType.REGULAR.value,
                total_votes=70,
                winner_count=1,
                candidates=[regular_candidate, regular_candidate_2],
            )
        ],
        house_results=[
            HouseResultRow(
                house_id="house-1",
                house_name="Pallava",
                vote_count=30,
                percentage=30.0,
                positions=[
                    PositionResultRow(
                        position_id="pos-2",
                        position_name="House Captain",
                        election_type=ElectionType.HOUSE.value,
                        total_votes=30,
                        winner_count=1,
                        candidates=[house_candidate],
                    )
                ],
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


def _make_report_service(tmp_path: Path, **overrides) -> ReportService:
    election = MagicMock()
    election.id = "election-1"
    election.election_name = "Student Council 2026"
    election.deleted_at = None

    election_repo = overrides.get("election_repository", MagicMock())
    election_repo.get_by_id.return_value = election

    report_repo = MagicMock()
    report_repo.add.side_effect = lambda report: report

    service = ReportService(
        report_repository=report_repo,
        report_download_repository=MagicMock(),
        audit_log_repository=MagicMock(),
        election_repository=election_repo,
        position_repository=MagicMock(),
        candidate_repository=MagicMock(),
        house_repository=MagicMock(),
        node_repository=MagicMock(),
        vote_repository=MagicMock(),
        settings_repository=MagicMock(),
        theme_repository=MagicMock(),
        user_repository=MagicMock(),
    )
    service.data_collector = MagicMock()
    service.data_collector.collect.return_value = _sample_snapshot()
    service._build_output_path = lambda election_id, report_type: tmp_path / f"report{service._EXTENSIONS[report_type]}"
    return service


def test_report_data_collector_marks_winners() -> None:
    election = MagicMock()
    election.id = "election-1"
    election.election_name = "Student Council 2026"
    election.academic_year = "2025-26"
    election.status = ElectionStatus.COMPLETED
    election.deleted_at = None

    position = MagicMock()
    position.id = "pos-1"
    position.position_name = "School Pupil Leader"
    position.election_type = ElectionType.REGULAR
    position.winner_count = 1

    candidate_a = MagicMock()
    candidate_a.id = "cand-1"
    candidate_a.candidate_name = "Alice"
    candidate_a.position_id = "pos-1"
    candidate_a.house_id = None

    candidate_b = MagicMock()
    candidate_b.id = "cand-2"
    candidate_b.candidate_name = "Bob"
    candidate_b.position_id = "pos-1"
    candidate_b.house_id = None

    election_repo = MagicMock()
    election_repo.get_by_id.return_value = election

    position_repo = MagicMock()
    position_repo.list_for_election.return_value = [position]

    candidate_repo = MagicMock()
    candidate_repo.list_for_election.return_value = [candidate_a, candidate_b]

    vote_repo = MagicMock()
    vote_repo.count_by_candidate.return_value = [("cand-1", "pos-1", 60), ("cand-2", "pos-1", 40)]
    vote_repo.count_by_house.return_value = []
    vote_repo.count_by_node.return_value = []
    vote_repo.count_for_election.return_value = 100

    collector = ReportDataCollector(
        election_repository=election_repo,
        position_repository=position_repo,
        candidate_repository=candidate_repo,
        house_repository=MagicMock(),
        node_repository=MagicMock(),
        vote_repository=vote_repo,
        settings_repository=MagicMock(),
        theme_repository=MagicMock(),
    )
    collector.theme_repository.get_active.return_value = MagicMock(school_name="VNPS")
    collector.house_repository.list_all_ordered.return_value = []
    collector.node_repository.list_all_ordered.return_value = []

    snapshot = collector.collect("election-1", generated_by="Admin")

    assert snapshot.summary.total_votes == 100
    assert snapshot.final_results[0].candidates[0].candidate_name == "Alice"
    assert snapshot.final_results[0].candidates[0].is_winner is True
    assert snapshot.final_results[0].candidates[1].is_winner is False
    assert len(snapshot.candidate_reports) == 2


@pytest.mark.parametrize(
    ("generator_cls", "extension"),
    [
        (ExcelReportGenerator, ".xlsx"),
        (CsvReportGenerator, ".csv"),
        (PdfReportGenerator, ".pdf"),
    ],
)
def test_generators_write_files(tmp_path: Path, generator_cls, extension: str) -> None:
    output_path = tmp_path / f"report{extension}"
    generator_cls().generate(_sample_snapshot(), output_path)
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_report_persists_metadata(tmp_path: Path) -> None:
    service = _make_report_service(tmp_path)
    user = MagicMock()
    user.full_name = "Admin User"
    user.username = "admin"
    service.user_repository.get_by_id.return_value = user
    response = service.generate_report(
        "election-1",
        ReportType.CSV,
        user_id="user-1",
        generated_by_name="Admin User",
    )

    assert response.report_type == ReportType.CSV
    assert response.election_name == "Student Council 2026"
    service.report_repository.add.assert_called_once()


def test_generate_report_rejects_missing_election(tmp_path: Path) -> None:
    service = _make_report_service(tmp_path)
    service.election_repository.get_by_id.return_value = None

    with pytest.raises(NotFoundError, match="Election not found"):
        service.generate_report(
            "missing",
            ReportType.PDF,
            user_id="user-1",
            generated_by_name="Admin User",
        )


def test_get_download_path_requires_existing_file(tmp_path: Path) -> None:
    service = _make_report_service(tmp_path)
    report = MagicMock()
    report.id = "report-1"
    report.deleted_at = None
    report.report_type = ReportType.CSV
    report.file_path = str(tmp_path / "missing.csv")
    service.report_repository.get_by_id.return_value = report

    with pytest.raises(NotFoundError, match="Report file not found"):
        service.get_download_path("report-1")
