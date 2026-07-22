"""Report generator base interface."""

from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas.report import ReportDataSnapshot


class BaseReportGenerator(ABC):
    """Abstract report file generator."""

    @abstractmethod
    def generate(self, data: ReportDataSnapshot, output_path: Path) -> None:
        """Write the report file to the given path."""
