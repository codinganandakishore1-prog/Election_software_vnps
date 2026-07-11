"""Report repository."""

from sqlalchemy.orm import Session

from app.models.report import Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """Data access for report records."""

    model = Report

    def __init__(self, db: Session) -> None:
        super().__init__(db)
