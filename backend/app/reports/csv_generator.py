"""CSV report generator."""

from __future__ import annotations

import csv
from pathlib import Path

from app.reports.base import BaseReportGenerator
from app.schemas.report import ReportDataSnapshot


class CsvReportGenerator(BaseReportGenerator):
    """Generates a UTF-8 CSV file with candidate-level results."""

    def generate(self, data: ReportDataSnapshot, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = data.summary.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")

        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "Election",
                    "Position",
                    "House",
                    "Candidate",
                    "Votes",
                    "Percentage",
                    "Winner",
                    "Timestamp",
                ]
            )
            for candidate in data.candidate_reports:
                writer.writerow(
                    [
                        data.summary.election_name,
                        candidate.position_name,
                        candidate.house_name or "",
                        candidate.candidate_name,
                        candidate.vote_count,
                        f"{candidate.percentage}%",
                        "Yes" if candidate.is_winner else "No",
                        timestamp,
                    ]
                )
