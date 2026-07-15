"""Report repositories."""

from datetime import datetime

from election_platform.enums.admin import ReportType
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.report import Report, ReportDownload, ReportTemplate
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """Data access for report records."""

    model = Report

    def list_for_election(self, election_id: str) -> list[Report]:
        stmt = (
            select(Report)
            .where(Report.election_id == election_id, Report.deleted_at.is_(None))
            .order_by(Report.generated_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_type(self, election_id: str, report_type: ReportType) -> list[Report]:
        stmt = select(Report).where(
            Report.election_id == election_id,
            Report.report_type == report_type,
            Report.deleted_at.is_(None),
        )
        return list(self.db.scalars(stmt).all())

    def list_filtered(
        self,
        *,
        election_id: str | None = None,
        report_type: ReportType | None = None,
        generated_after: datetime | None = None,
        generated_before: datetime | None = None,
        limit: int | None = None,
    ) -> list[Report]:
        stmt = select(Report).where(Report.deleted_at.is_(None))

        if election_id is not None:
            stmt = stmt.where(Report.election_id == election_id)
        if report_type is not None:
            stmt = stmt.where(Report.report_type == report_type)
        if generated_after is not None:
            stmt = stmt.where(Report.generated_at >= generated_after)
        if generated_before is not None:
            stmt = stmt.where(Report.generated_at <= generated_before)

        stmt = stmt.order_by(Report.generated_at.desc())
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())


class ReportDownloadRepository(BaseRepository[ReportDownload]):
    """Data access for report download audit records."""

    model = ReportDownload

    def list_for_report(self, report_id: str) -> list[ReportDownload]:
        return self.list_by_field("report_id", report_id)


class ReportTemplateRepository(BaseRepository[ReportTemplate]):
    """Data access for report template records."""

    model = ReportTemplate

    def list_active(self, *, limit: int | None = None, offset: int = 0) -> list[ReportTemplate]:
        return self.list_by_field("active", True, limit=limit, offset=offset)

    def list_by_type(self, report_type: ReportType) -> list[ReportTemplate]:
        return self.list_by_field("report_type", report_type)
