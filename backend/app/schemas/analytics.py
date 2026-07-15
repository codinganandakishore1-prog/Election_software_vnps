"""Analytics response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.report import HouseResultRow, PositionResultRow


class VoteCountEntry(BaseModel):
    """Vote tally for a single candidate."""

    candidate_id: str
    candidate_name: str
    position_id: str
    position_name: str
    vote_count: int
    percentage: float = 0.0
    rank: int = 0
    is_winner: bool = False


class PositionResults(BaseModel):
    """Aggregated results for one position."""

    position_id: str
    position_name: str
    election_type: str = "Regular"
    total_votes: int
    winner_count: int = 1
    candidates: list[VoteCountEntry]


class NodeHealthEntry(BaseModel):
    """Node health row for dashboard and monitoring."""

    node_id: str
    name: str
    status: str
    votes: int
    queue: int
    sync_status: str | None = None
    last_heartbeat: datetime | None = None


class ActivityEntry(BaseModel):
    """Recent activity feed item."""

    time: str
    message: str
    event_type: str = "info"


class VotesPerMinuteEntry(BaseModel):
    """Votes-per-minute chart data point."""

    minute: str
    count: int


class TimelineEntry(BaseModel):
    """Voting activity over time."""

    label: str
    count: int


class TurnoutStats(BaseModel):
    """Turnout based on estimated participation vs eligible voters."""

    eligible_voters: int | None = None
    estimated_participants: int = 0
    turnout_percentage: float | None = None
    regular_participants: int = 0
    house_participants: int = 0


class LeadingCandidateEntry(BaseModel):
    """Current leader for a position with margin of victory."""

    position_id: str
    position_name: str
    candidate_id: str
    candidate_name: str
    vote_count: int
    percentage: float
    margin: float = 0.0


class NodePerformanceEntry(BaseModel):
    """Per-node vote contribution and health metrics."""

    node_id: str
    node_name: str
    election_type: str
    house_name: str | None = None
    vote_count: int
    contribution_percentage: float = 0.0
    status: str = "Unknown"
    sync_status: str | None = None
    queue_size: int = 0
    last_heartbeat: datetime | None = None
    votes_per_hour: float | None = None


class AnalyticsSummary(BaseModel):
    """High-level election analytics summary."""

    election_id: str | None = None
    election_name: str = "No active election"
    election_status: str = "Draft"
    total_votes: int = 0
    regular_votes: int = 0
    house_votes: int = 0
    online_nodes: int = 0
    total_nodes: int = 0
    position_count: int = 0
    candidate_count: int = 0
    turnout: TurnoutStats = Field(default_factory=TurnoutStats)
    updated_at: datetime | None = None


class DashboardSnapshot(BaseModel):
    """Full dashboard state for REST and WebSocket snapshots."""

    election_name: str = "No active election"
    election_status: str = "Draft"
    total_votes: int = 0
    online_nodes: int = 0
    total_nodes: int = 0
    pending_queue: int = 0
    sync_errors: int = 0
    last_vote_time: datetime | None = None
    connected_clients: int = 0
    nodes: list[NodeHealthEntry] = Field(default_factory=list)
    activity: list[ActivityEntry] = Field(default_factory=list)
    votes_per_minute: list[VotesPerMinuteEntry] = Field(default_factory=list)


class LiveResultsSnapshot(BaseModel):
    """Public live results payload."""

    election_id: str | None = None
    election_name: str = "No active election"
    election_status: str = "Draft"
    total_votes: int = 0
    updated_at: datetime | None = None
    positions: list[PositionResults] = Field(default_factory=list)


class RegularAnalyticsSnapshot(BaseModel):
    """Regular election analytics with rankings."""

    election_id: str | None = None
    election_name: str = "No active election"
    election_status: str = "Draft"
    total_votes: int = 0
    turnout: TurnoutStats = Field(default_factory=TurnoutStats)
    positions: list[PositionResultRow] = Field(default_factory=list)
    leading_candidates: list[LeadingCandidateEntry] = Field(default_factory=list)
    updated_at: datetime | None = None


class HouseAnalyticsSnapshot(BaseModel):
    """House election analytics across all houses."""

    election_id: str | None = None
    election_name: str = "No active election"
    election_status: str = "Draft"
    total_votes: int = 0
    house_results: list[HouseResultRow] = Field(default_factory=list)
    updated_at: datetime | None = None


class NodePerformanceSnapshot(BaseModel):
    """Node contribution and performance analytics."""

    election_id: str | None = None
    election_name: str = "No active election"
    total_votes: int = 0
    nodes: list[NodePerformanceEntry] = Field(default_factory=list)
    updated_at: datetime | None = None


class TimelineSnapshot(BaseModel):
    """Voting activity timeline for charts."""

    election_id: str | None = None
    election_name: str = "No active election"
    interval: str = "minute"
    points: list[TimelineEntry] = Field(default_factory=list)
    updated_at: datetime | None = None


class AnalyticsOverviewSnapshot(BaseModel):
    """Complete analytics overview for the admin analytics page."""

    summary: AnalyticsSummary
    regular_positions: list[PositionResultRow] = Field(default_factory=list)
    house_results: list[HouseResultRow] = Field(default_factory=list)
    node_statistics: list[NodePerformanceEntry] = Field(default_factory=list)
    leading_candidates: list[LeadingCandidateEntry] = Field(default_factory=list)
    votes_per_minute: list[VotesPerMinuteEntry] = Field(default_factory=list)
    timeline: list[TimelineEntry] = Field(default_factory=list)
