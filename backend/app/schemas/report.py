"""Report request/response schemas."""

from datetime import datetime

from election_platform.enums.admin import ReportType
from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    """Payload for generating a report."""

    election_id: str
    format: ReportType


class ReportResponse(BaseModel):
    """Generated report metadata."""

    id: str
    election_id: str
    election_name: str
    report_name: str
    report_type: ReportType
    file_size: int | None = None
    generated_by: str | None = None
    generated_by_name: str | None = None
    generated_at: datetime


class CandidateReportRow(BaseModel):
    """Candidate-level result row."""

    candidate_id: str
    candidate_name: str
    position_id: str
    position_name: str
    election_type: str
    house_name: str | None = None
    vote_count: int
    percentage: float = 0.0
    is_winner: bool = False
    rank: int = 0


class PositionResultRow(BaseModel):
    """Position-level aggregated results."""

    position_id: str
    position_name: str
    election_type: str
    total_votes: int
    winner_count: int
    candidates: list[CandidateReportRow] = Field(default_factory=list)


class HouseResultRow(BaseModel):
    """House-level vote distribution and leadership results."""

    house_id: str
    house_name: str
    vote_count: int
    percentage: float
    positions: list[PositionResultRow] = Field(default_factory=list)


class NodeStatisticRow(BaseModel):
    """Per-node vote statistics."""

    node_id: str
    node_name: str
    election_type: str
    house_name: str | None = None
    vote_count: int


class VoteSummary(BaseModel):
    """Election-wide vote summary."""

    election_id: str
    election_name: str
    academic_year: str | None = None
    election_status: str
    total_votes: int
    regular_votes: int
    house_votes: int
    position_count: int
    candidate_count: int
    generated_at: datetime
    generated_by: str
    school_name: str


class ReportDataSnapshot(BaseModel):
    """Complete dataset for report generation."""

    summary: VoteSummary
    final_results: list[PositionResultRow] = Field(default_factory=list)
    regular_results: list[PositionResultRow] = Field(default_factory=list)
    house_results: list[HouseResultRow] = Field(default_factory=list)
    candidate_reports: list[CandidateReportRow] = Field(default_factory=list)
    node_statistics: list[NodeStatisticRow] = Field(default_factory=list)
