"""House management service."""

from __future__ import annotations

from election_platform.enums.election import ElectionStatus, ElectionType

from app.database.seeds import new_uuid
from app.exceptions.base import ElectionLockedError, NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.position import Position
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.election_repository import ElectionRepository
from app.repositories.house_repository import HouseRepository
from app.repositories.node_repository import NodeRepository
from app.repositories.position_repository import PositionRepository
from app.schemas.house import (
    HouseCandidateResponse,
    HouseConfigurationRequest,
    HouseConfigurationResponse,
    HousePositionSummary,
    HouseResponse,
    HouseValidationResponse,
)
from app.services.base import BaseService


class HouseService(BaseService):
    """Handles houses, house configuration, and validation."""

    def __init__(
        self,
        house_repository: HouseRepository,
        position_repository: PositionRepository,
        candidate_repository: CandidateRepository,
        election_repository: ElectionRepository,
        node_repository: NodeRepository,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        self.house_repository = house_repository
        self.position_repository = position_repository
        self.candidate_repository = candidate_repository
        self.election_repository = election_repository
        self.node_repository = node_repository
        self.audit_log_repository = audit_log_repository

    def list_house_names(self) -> list[str]:
        """Return active house names per SRS GET /houses."""
        return [house.house_name for house in self.house_repository.list_all_ordered()]

    def list_houses(self) -> list[HouseResponse]:
        """Return full house records."""
        return [self._to_house_response(house) for house in self.house_repository.list_all_ordered()]

    def get_configuration(self, election_id: str) -> HouseConfigurationResponse:
        """Return house positions and coverage for an election."""
        self._ensure_election_exists(election_id)
        houses = self.list_houses()
        positions = self.position_repository.list_by_election_type(election_id, ElectionType.HOUSE)
        summaries = [self._position_summary(position, houses) for position in positions]
        return HouseConfigurationResponse(
            election_id=election_id,
            positions=summaries,
            houses=houses,
        )

    def configure_positions(
        self,
        payload: HouseConfigurationRequest,
        *,
        user_id: str | None = None,
    ) -> HouseConfigurationResponse:
        """Configure shared house leadership positions for all four houses."""
        self._ensure_election_editable(payload.election_id)

        cleaned_names = [name.strip() for name in payload.positions if name.strip()]
        if not cleaned_names:
            raise ValidationError("At least one house position is required")

        if len(cleaned_names) != len(set(name.lower() for name in cleaned_names)):
            raise ValidationError("Duplicate house position names are not allowed")

        existing = self.position_repository.list_by_election_type(payload.election_id, ElectionType.HOUSE)
        existing_by_name = {position.position_name.lower(): position for position in existing}
        requested_names = {name.lower() for name in cleaned_names}

        for index, name in enumerate(cleaned_names, start=1):
            current = existing_by_name.get(name.lower())
            if current is None:
                position = Position(
                    id=new_uuid(),
                    election_id=payload.election_id,
                    election_type=ElectionType.HOUSE,
                    position_name=name,
                    winner_count=1,
                    display_order=index,
                    active=True,
                )
                self.position_repository.add(position)
            else:
                current.position_name = name
                current.display_order = index
                current.active = True

        for position in existing:
            if position.position_name.lower() not in requested_names:
                candidate_count = len(self.candidate_repository.list_for_position(position.id))
                if candidate_count > 0:
                    raise ValidationError(
                        f'Cannot remove position "{position.position_name}" while candidates are assigned'
                    )
                self.position_repository.soft_delete(position)

        self._audit(
            user_id,
            "House Configuration Updated",
            {"election_id": payload.election_id, "positions": cleaned_names},
        )
        self.position_repository.commit()
        return self.get_configuration(payload.election_id)

    def list_house_candidates(
        self,
        election_id: str,
        *,
        house_id: str | None = None,
    ) -> list[HouseCandidateResponse]:
        """List house election candidates, optionally filtered by house."""
        self._ensure_election_exists(election_id)
        candidates = self.candidate_repository.list_for_house(
            election_id,
            house_id=house_id,
        )
        return [self._to_house_candidate_response(candidate) for candidate in candidates]

    def validate(self, election_id: str) -> HouseValidationResponse:
        """Validate house configuration, candidates, and node assignments."""
        errors: list[str] = []

        election = self.election_repository.get_by_id(election_id)
        if election is None or election.deleted_at is not None:
            return HouseValidationResponse(valid=False, errors=["Election not found"])

        houses = self.house_repository.list_all_ordered()
        if len(houses) < 4:
            errors.append("All four school houses must be configured")

        positions = self.position_repository.list_by_election_type(election_id, ElectionType.HOUSE, include_inactive=False)
        if not positions:
            errors.append("House configuration must include at least one leadership position")
        else:
            errors.extend(self._validate_house_candidates(election_id, positions, houses))

        errors.extend(self._validate_node_assignments())

        return HouseValidationResponse(valid=not errors, errors=errors)

    def _validate_house_candidates(
        self,
        election_id: str,
        positions: list[Position],
        houses: list,
    ) -> list[str]:
        errors: list[str] = []

        for position in positions:
            for house in houses:
                candidates = [
                    candidate
                    for candidate in self.candidate_repository.list_for_position(position.id)
                    if candidate.house_id == house.id and candidate.deleted_at is None
                ]
                if not candidates:
                    errors.append(
                        f'Position "{position.position_name}" has no candidates for house {house.house_name}'
                    )
                    continue

                for candidate in candidates:
                    if not candidate.image_id:
                        errors.append(
                            f'Candidate "{candidate.candidate_name}" ({house.house_name}, '
                            f'{position.position_name}) is missing a photo'
                        )

                names = [candidate.candidate_name.lower() for candidate in candidates]
                if len(names) != len(set(names)):
                    errors.append(
                        f'Duplicate candidate names found for {position.position_name} in {house.house_name}'
                    )

        house_candidates = self.candidate_repository.list_for_election_type(election_id, ElectionType.HOUSE)
        for candidate in house_candidates:
            if candidate.house_id is None:
                errors.append(f'House candidate "{candidate.candidate_name}" is missing house assignment')
            if not candidate.image_id:
                if not any(
                    error.startswith(f'Candidate "{candidate.candidate_name}"')
                    for error in errors
                ):
                    errors.append(f'House candidate "{candidate.candidate_name}" is missing a photo')

        return errors

    def _validate_node_assignments(self) -> list[str]:
        errors: list[str] = []
        nodes = self.node_repository.list_all_ordered()

        house_nodes = [node for node in nodes if node.election_type == ElectionType.HOUSE and node.active]
        regular_nodes = [node for node in nodes if node.election_type == ElectionType.REGULAR and node.active]

        if not house_nodes:
            errors.append("No active house voting nodes are registered")
        else:
            for node in house_nodes:
                if not node.house_id:
                    errors.append(f'House node "{node.node_name}" is missing an assigned house')

        for node in regular_nodes:
            if node.house_id is not None:
                errors.append(f'Regular node "{node.node_name}" must not have a house assignment')

        return errors

    def _position_summary(self, position: Position, houses: list[HouseResponse]) -> HousePositionSummary:
        counts: dict[str, int] = {}
        candidates = self.candidate_repository.list_for_position(position.id)
        for house in houses:
            counts[house.id] = sum(
                1 for candidate in candidates if candidate.house_id == house.id and candidate.deleted_at is None
            )
        return HousePositionSummary(
            id=position.id,
            position_name=position.position_name,
            display_order=position.display_order,
            winner_count=position.winner_count,
            active=position.active,
            candidate_count_by_house=counts,
        )

    def _to_house_response(self, house) -> HouseResponse:
        return HouseResponse(
            id=house.id,
            house_name=house.house_name,
            color=house.color,
            logo_path=house.logo_path,
            active=house.active,
        )

    def _to_house_candidate_response(self, candidate) -> HouseCandidateResponse:
        return HouseCandidateResponse(
            id=candidate.id,
            election_id=candidate.election_id,
            position_id=candidate.position_id,
            position_name=candidate.position.position_name,
            house_id=candidate.house_id or "",
            house_name=candidate.house.house_name if candidate.house else "",
            candidate_name=candidate.candidate_name,
            display_order=candidate.display_order,
            status=candidate.status.value,
            has_image=candidate.image_id is not None,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at,
        )

    def _ensure_election_exists(self, election_id: str) -> None:
        election = self.election_repository.get_by_id(election_id)
        if election is None or election.deleted_at is not None:
            raise NotFoundError("Election not found")

    def _ensure_election_editable(self, election_id: str) -> None:
        election = self.election_repository.get_by_id(election_id)
        if election is None or election.deleted_at is not None:
            raise NotFoundError("Election not found")
        if election.status == ElectionStatus.LIVE:
            raise ElectionLockedError("Cannot modify house configuration while the election is live")
        if election.configuration_locked is True:
            raise ElectionLockedError("Election configuration is locked")

    def _audit(self, user_id: str | None, action: str, details: dict | None) -> None:
        if not user_id:
            return
        self.audit_log_repository.add(
            AuditLog(
                id=new_uuid(),
                user_id=user_id,
                module="Houses",
                action=action,
                new_value=details,
            )
        )
