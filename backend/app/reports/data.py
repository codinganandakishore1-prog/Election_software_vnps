"""Report data aggregation from election vote records."""

from __future__ import annotations

from election_platform.enums.election import ElectionType

from app.database.base import utc_now
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.election_repository import ElectionRepository
from app.repositories.house_repository import HouseRepository
from app.repositories.node_repository import NodeRepository
from app.repositories.position_repository import PositionRepository
from app.repositories.settings_repository import SettingsRepository, ThemeRepository
from app.repositories.vote_repository import VoteRepository
from app.schemas.report import (
    CandidateReportRow,
    HouseResultRow,
    NodeStatisticRow,
    PositionResultRow,
    ReportDataSnapshot,
    VoteSummary,
)


class ReportDataCollector:
    """Builds a report snapshot from repository data."""

    def __init__(
        self,
        election_repository: ElectionRepository,
        position_repository: PositionRepository,
        candidate_repository: CandidateRepository,
        house_repository: HouseRepository,
        node_repository: NodeRepository,
        vote_repository: VoteRepository,
        settings_repository: SettingsRepository,
        theme_repository: ThemeRepository,
    ) -> None:
        self.election_repository = election_repository
        self.position_repository = position_repository
        self.candidate_repository = candidate_repository
        self.house_repository = house_repository
        self.node_repository = node_repository
        self.vote_repository = vote_repository
        self.settings_repository = settings_repository
        self.theme_repository = theme_repository

    def collect(self, election_id: str, *, generated_by: str) -> ReportDataSnapshot:
        election = self.election_repository.get_by_id(election_id)
        if election is None or election.deleted_at is not None:
            raise ValueError("Election not found")

        tally_map = {
            (candidate_id, position_id): count
            for candidate_id, position_id, count in self.vote_repository.count_by_candidate(election_id)
        }
        house_vote_map = {
            house_id: count for house_id, count in self.vote_repository.count_by_house(election_id)
        }
        node_vote_map = {
            node_id: count for node_id, count in self.vote_repository.count_by_node(election_id)
        }

        positions = self.position_repository.list_for_election(election_id)
        candidates = self.candidate_repository.list_for_election(election_id)
        houses = self.house_repository.list_all_ordered()
        nodes = self.node_repository.list_all_ordered()

        house_name_map = {house.id: house.house_name for house in houses}
        school_name = self._resolve_school_name()

        regular_results: list[PositionResultRow] = []
        house_position_results: list[PositionResultRow] = []
        final_results: list[PositionResultRow] = []
        candidate_reports: list[CandidateReportRow] = []

        for position in positions:
            position_candidates = [
                candidate for candidate in candidates if candidate.position_id == position.id
            ]
            position_row = self._build_position_results(
                position,
                position_candidates,
                tally_map,
                house_name_map,
            )
            final_results.append(position_row)
            candidate_reports.extend(position_row.candidates)

            if position.election_type == ElectionType.REGULAR:
                regular_results.append(position_row)
            else:
                house_position_results.append(position_row)

        total_votes = self.vote_repository.count_for_election(election_id)
        regular_votes = sum(row.total_votes for row in regular_results)
        house_votes = sum(row.total_votes for row in house_position_results)

        house_results: list[HouseResultRow] = []
        for house in houses:
            unique_positions: dict[str, PositionResultRow] = {}
            for position_row in house_position_results:
                house_candidates = [
                    candidate
                    for candidate in position_row.candidates
                    if candidate.house_name == house.house_name
                ]
                if house_candidates:
                    unique_positions[position_row.position_id] = PositionResultRow(
                        position_id=position_row.position_id,
                        position_name=position_row.position_name,
                        election_type=position_row.election_type,
                        total_votes=sum(candidate.vote_count for candidate in house_candidates),
                        winner_count=position_row.winner_count,
                        candidates=house_candidates,
                    )

            house_vote_count = house_vote_map.get(house.id, 0)
            house_results.append(
                HouseResultRow(
                    house_id=house.id,
                    house_name=house.house_name,
                    vote_count=house_vote_count,
                    percentage=round((house_vote_count / total_votes) * 100, 1) if total_votes else 0.0,
                    positions=list(unique_positions.values()),
                )
            )

        node_statistics: list[NodeStatisticRow] = []
        for node in nodes:
            node_statistics.append(
                NodeStatisticRow(
                    node_id=node.id,
                    node_name=node.node_name,
                    election_type=node.election_type.value,
                    house_name=house_name_map.get(node.house_id) if node.house_id else None,
                    vote_count=node_vote_map.get(node.id, 0),
                )
            )

        summary = VoteSummary(
            election_id=election.id,
            election_name=election.election_name,
            academic_year=election.academic_year,
            election_status=election.status.value,
            total_votes=total_votes,
            regular_votes=regular_votes,
            house_votes=house_votes,
            position_count=len(positions),
            candidate_count=len(candidates),
            generated_at=utc_now(),
            generated_by=generated_by,
            school_name=school_name,
        )

        return ReportDataSnapshot(
            summary=summary,
            final_results=final_results,
            regular_results=regular_results,
            house_results=house_results,
            candidate_reports=candidate_reports,
            node_statistics=node_statistics,
        )

    def _resolve_school_name(self) -> str:
        theme = self.theme_repository.get_active()
        if theme and theme.school_name:
            return theme.school_name
        settings = self.settings_repository.get_active()
        if settings and settings.school_name:
            return settings.school_name
        return "Election Management Platform"

    def _build_position_results(
        self,
        position,
        position_candidates: list,
        tally_map: dict[tuple[str, str], int],
        house_name_map: dict[str, str],
    ) -> PositionResultRow:
        rows: list[CandidateReportRow] = []
        position_total = 0

        for candidate in position_candidates:
            vote_count = tally_map.get((candidate.id, position.id), 0)
            position_total += vote_count
            house_name = house_name_map.get(candidate.house_id) if candidate.house_id else None
            rows.append(
                CandidateReportRow(
                    candidate_id=candidate.id,
                    candidate_name=candidate.candidate_name,
                    position_id=position.id,
                    position_name=position.position_name,
                    election_type=position.election_type.value,
                    house_name=house_name,
                    vote_count=vote_count,
                )
            )

        rows.sort(key=lambda item: (-item.vote_count, item.candidate_name))
        for index, row in enumerate(rows, start=1):
            row.rank = index
            row.percentage = round((row.vote_count / position_total) * 100, 1) if position_total else 0.0
            row.is_winner = index <= position.winner_count and row.vote_count > 0

        return PositionResultRow(
            position_id=position.id,
            position_name=position.position_name,
            election_type=position.election_type.value,
            total_votes=position_total,
            winner_count=position.winner_count,
            candidates=rows,
        )
