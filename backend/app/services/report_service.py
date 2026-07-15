"""Report generation service."""

from __future__ import annotations

import re
from pathlib import Path

from election_platform.enums.admin import ReportType

from app.config.settings import settings
from app.database.base import utc_now
from app.database.seeds import new_uuid
from app.exceptions.base import NotFoundError
from app.models.audit_log import AuditLog
from app.models.report import Report, ReportDownload
from app.reports.csv_generator import CsvReportGenerator
from app.reports.data import ReportDataCollector
from app.reports.excel_generator import ExcelReportGenerator
from app.reports.pdf_generator import PdfReportGenerator
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.election_repository import ElectionRepository
from app.repositories.house_repository import HouseRepository
from app.repositories.node_repository import NodeRepository
from app.repositories.position_repository import PositionRepository
from app.repositories.report_repository import ReportDownloadRepository, ReportRepository
from app.repositories.settings_repository import SettingsRepository, ThemeRepository
from app.repositories.user_repository import UserRepository
from app.repositories.vote_repository import VoteRepository
from app.schemas.report import ReportDataSnapshot, ReportResponse
from app.services.base import BaseService


class ReportService(BaseService):
    """Handles report generation and export."""

    _GENERATORS = {
        ReportType.EXCEL: ExcelReportGenerator(),
        ReportType.CSV: CsvReportGenerator(),
        ReportType.PDF: PdfReportGenerator(),
    }

    _EXTENSIONS = {
        ReportType.EXCEL: ".xlsx",
        ReportType.CSV: ".csv",
        ReportType.PDF: ".pdf",
    }

    _MEDIA_TYPES = {
        ReportType.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ReportType.CSV: "text/csv",
        ReportType.PDF: "application/pdf",
    }

    def __init__(
        self,
        report_repository: ReportRepository,
        report_download_repository: ReportDownloadRepository,
        audit_log_repository: AuditLogRepository,
        election_repository: ElectionRepository,
        position_repository: PositionRepository,
        candidate_repository: CandidateRepository,
        house_repository: HouseRepository,
        node_repository: NodeRepository,
        vote_repository: VoteRepository,
        settings_repository: SettingsRepository,
        theme_repository: ThemeRepository,
        user_repository: UserRepository,
    ) -> None:
        self.report_repository = report_repository
        self.report_download_repository = report_download_repository
        self.audit_log_repository = audit_log_repository
        self.election_repository = election_repository
        self.user_repository = user_repository
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

    def list_reports(
        self,
        *,
        election_id: str | None = None,
        report_type: ReportType | None = None,
    ) -> list[ReportResponse]:
        reports = self.report_repository.list_filtered(
            election_id=election_id,
            report_type=report_type,
        )
        return [self._to_response(report) for report in reports]

    def generate_report(
        self,
        election_id: str,
        report_type: ReportType,
        *,
        user_id: str | None,
        generated_by_name: str,
    ) -> ReportResponse:
        election = self.election_repository.get_by_id(election_id)
        if election is None or election.deleted_at is not None:
            raise NotFoundError("Election not found")

        snapshot = self.data_collector.collect(
            election_id,
            generated_by=generated_by_name,
        )
        output_path = self._build_output_path(election_id, report_type)
        generator = self._GENERATORS[report_type]
        generator.generate(snapshot, output_path)

        file_size = output_path.stat().st_size
        report_name = self._build_report_name(election.election_name, report_type)
        report = Report(
            id=new_uuid(),
            election_id=election_id,
            report_name=report_name,
            report_type=report_type,
            file_path=str(output_path),
            generated_by=user_id,
            generated_at=utc_now(),
            file_size=file_size,
        )
        self.report_repository.add(report)
        self._audit(
            user_id,
            "Generate Report",
            {
                "report_id": report.id,
                "election_id": election_id,
                "report_type": report_type.value,
                "file_path": str(output_path),
            },
        )
        return self._to_response(report, election_name=election.election_name)

    def get_report(self, report_id: str) -> Report:
        report = self.report_repository.get_by_id(report_id)
        if report is None or report.deleted_at is not None:
            raise NotFoundError("Report not found")
        return report

    def get_download_path(self, report_id: str) -> tuple[Path, str, str]:
        report = self.get_report(report_id)
        file_path = Path(report.file_path)
        if not file_path.exists():
            raise NotFoundError("Report file not found on disk")
        media_type = self._MEDIA_TYPES[report.report_type]
        filename = file_path.name
        return file_path, media_type, filename

    def record_download(
        self,
        report_id: str,
        *,
        user_id: str | None,
        ip_address: str | None = None,
    ) -> None:
        self.get_report(report_id)
        self.report_download_repository.add(
            ReportDownload(
                id=new_uuid(),
                report_id=report_id,
                downloaded_by=user_id,
                downloaded_at=utc_now(),
                ip_address=ip_address,
            )
        )
        self._audit(
            user_id,
            "Download Report",
            {"report_id": report_id, "ip_address": ip_address},
        )

    def build_snapshot(self, election_id: str, *, generated_by: str) -> ReportDataSnapshot:
        """Expose report data for tests and analytics reuse."""
        return self.data_collector.collect(election_id, generated_by=generated_by)

    def _build_output_path(self, election_id: str, report_type: ReportType) -> Path:
        subfolder = {
            ReportType.EXCEL: "excel",
            ReportType.CSV: "csv",
            ReportType.PDF: "pdf",
        }[report_type]
        timestamp = utc_now().strftime("%Y%m%d_%H%M%S")
        filename = f"{election_id}_{timestamp}{self._EXTENSIONS[report_type]}"
        return settings.report_folder / subfolder / filename

    def _build_report_name(self, election_name: str, report_type: ReportType) -> str:
        safe_name = re.sub(r"[^\w\s-]", "", election_name).strip().replace(" ", "_")
        timestamp = utc_now().strftime("%Y-%m-%d %H:%M")
        return f"{safe_name}_{report_type.value}_{timestamp}"

    def _to_response(self, report: Report, *, election_name: str | None = None) -> ReportResponse:
        if election_name is None:
            election = self.election_repository.get_by_id(report.election_id)
            election_name = election.election_name if election else "Unknown Election"

        generator_name = None
        if report.generated_by:
            user = self.user_repository.get_by_id(report.generated_by)
            if user:
                generator_name = user.full_name or user.username

        return ReportResponse(
            id=report.id,
            election_id=report.election_id,
            election_name=election_name,
            report_name=report.report_name,
            report_type=report.report_type,
            file_size=report.file_size,
            generated_by=report.generated_by,
            generated_by_name=generator_name,
            generated_at=report.generated_at,
        )

    def _audit(self, user_id: str | None, action: str, details: dict | None) -> None:
        if not user_id:
            return
        self.audit_log_repository.add(
            AuditLog(
                id=new_uuid(),
                user_id=user_id,
                module="Reports",
                action=action,
                new_value=details,
            )
        )
