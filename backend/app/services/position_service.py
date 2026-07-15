"""Position management service."""

from __future__ import annotations

from election_platform.enums.election import ElectionStatus, ElectionType

from app.database.seeds import new_uuid
from app.exceptions.base import ElectionLockedError, NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.position import Position
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.election_repository import ElectionRepository
from app.repositories.position_repository import PositionRepository
from app.schemas.position import PositionCreate, PositionReorderRequest, PositionResponse, PositionUpdate
from app.services.base import BaseService


class PositionService(BaseService):
    """Handles position CRUD, status, and ordering operations."""

    def __init__(
        self,
        position_repository: PositionRepository,
        election_repository: ElectionRepository,
        candidate_repository: CandidateRepository,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        self.position_repository = position_repository
        self.election_repository = election_repository
        self.candidate_repository = candidate_repository
        self.audit_log_repository = audit_log_repository

    def list_positions(
        self,
        *,
        election_id: str | None = None,
        election_type: ElectionType | None = None,
        search: str | None = None,
        active: bool | None = None,
    ) -> list[PositionResponse]:
        positions = self.position_repository.list_filtered(
            election_id=election_id,
            election_type=election_type,
            search=search,
            active=active,
        )
        return [self._to_response(position) for position in positions]

    def get_position(self, position_id: str) -> PositionResponse:
        position = self._get_position_or_raise(position_id)
        return self._to_response(position)

    def create_position(self, payload: PositionCreate, *, user_id: str | None = None) -> PositionResponse:
        self._ensure_election_exists(payload.election_id)
        self._ensure_unique_name(payload.election_id, payload.election_type, payload.name)

        display_order = payload.display_order
        if display_order is None:
            display_order = self.position_repository.max_display_order(
                payload.election_id,
                payload.election_type,
            ) + 1

        position = Position(
            id=new_uuid(),
            election_id=payload.election_id,
            election_type=payload.election_type,
            position_name=payload.name.strip(),
            winner_count=payload.winner_count,
            display_order=display_order,
            active=True,
        )
        self.position_repository.add(position)
        self._audit(user_id, "Position Created", {"position_id": position.id, "position_name": position.position_name})
        self.position_repository.commit()
        return self._to_response(position)

    def update_position(
        self,
        position_id: str,
        payload: PositionUpdate,
        *,
        user_id: str | None = None,
    ) -> PositionResponse:
        position = self._get_position_or_raise(position_id)
        self._ensure_election_editable(position.election_id)

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise ValidationError("No fields provided to update")

        if "name" in updates:
            new_name = updates["name"].strip()
            self._ensure_unique_name(
                position.election_id,
                position.election_type,
                new_name,
                exclude_id=position.id,
            )
            position.position_name = new_name

        if "winner_count" in updates:
            position.winner_count = updates["winner_count"]

        if "display_order" in updates:
            position.display_order = updates["display_order"]

        self._audit(user_id, "Position Updated", {"position_id": position.id, **updates})
        self.position_repository.commit()
        return self._to_response(position)

    def delete_position(self, position_id: str, *, user_id: str | None = None) -> None:
        position = self._get_position_or_raise(position_id)
        self._ensure_election_editable(position.election_id)

        candidate_count = len(self.candidate_repository.list_for_position(position_id))
        if candidate_count > 0:
            raise ValidationError("Cannot delete a position with assigned candidates")

        self.position_repository.soft_delete(position)
        self._audit(
            user_id,
            "Position Deleted",
            {"position_id": position.id, "position_name": position.position_name},
        )
        self.position_repository.commit()

    def enable_position(self, position_id: str, *, user_id: str | None = None) -> PositionResponse:
        position = self._get_position_or_raise(position_id)
        position.active = True
        self._audit(user_id, "Position Enabled", {"position_id": position.id})
        self.position_repository.commit()
        return self._to_response(position)

    def disable_position(self, position_id: str, *, user_id: str | None = None) -> PositionResponse:
        position = self._get_position_or_raise(position_id)
        position.active = False
        self._audit(user_id, "Position Disabled", {"position_id": position.id})
        self.position_repository.commit()
        return self._to_response(position)

    def reorder_positions(self, payload: PositionReorderRequest, *, user_id: str | None = None) -> list[PositionResponse]:
        self._ensure_election_exists(payload.election_id)
        self._ensure_election_editable(payload.election_id)

        existing = self.position_repository.list_by_election_type(
            payload.election_id,
            payload.election_type,
        )
        existing_ids = {position.id for position in existing}
        ordered_ids = list(dict.fromkeys(payload.ordered_ids))

        if set(ordered_ids) != existing_ids:
            raise ValidationError("Reorder list must include every position for the election type exactly once")

        for index, position_id in enumerate(ordered_ids, start=1):
            position = self._get_position_or_raise(position_id)
            position.display_order = index

        self._audit(
            user_id,
            "Positions Reordered",
            {
                "election_id": payload.election_id,
                "election_type": payload.election_type.value,
                "ordered_ids": ordered_ids,
            },
        )
        self.position_repository.commit()

        refreshed = self.position_repository.list_by_election_type(payload.election_id, payload.election_type)
        return [self._to_response(position) for position in refreshed]

    def move_position(self, position_id: str, direction: str, *, user_id: str | None = None) -> PositionResponse:
        position = self._get_position_or_raise(position_id)
        self._ensure_election_editable(position.election_id)

        siblings = self.position_repository.list_by_election_type(position.election_id, position.election_type)
        index = next((idx for idx, item in enumerate(siblings) if item.id == position_id), None)
        if index is None:
            raise NotFoundError("Position not found")

        if direction == "up":
            if index == 0:
                raise ValidationError("Position is already at the top")
            swap_with = siblings[index - 1]
        elif direction == "down":
            if index == len(siblings) - 1:
                raise ValidationError("Position is already at the bottom")
            swap_with = siblings[index + 1]
        else:
            raise ValidationError("Direction must be 'up' or 'down'")

        position.display_order, swap_with.display_order = swap_with.display_order, position.display_order
        self._audit(user_id, f"Position Moved {direction.title()}", {"position_id": position.id})
        self.position_repository.commit()
        return self._to_response(position)

    def _get_position_or_raise(self, position_id: str) -> Position:
        position = self.position_repository.get_by_id(position_id)
        if position is None or position.deleted_at is not None:
            raise NotFoundError("Position not found")
        return position

    def _ensure_election_exists(self, election_id: str) -> None:
        election = self.election_repository.get_by_id(election_id)
        if election is None or election.deleted_at is not None:
            raise NotFoundError("Election not found")

    def _ensure_election_editable(self, election_id: str) -> None:
        election = self.election_repository.get_by_id(election_id)
        if election is None or election.deleted_at is not None:
            raise NotFoundError("Election not found")
        if election.status == ElectionStatus.LIVE:
            raise ElectionLockedError("Cannot modify positions while the election is live")
        if election.configuration_locked is True:
            raise ElectionLockedError("Election configuration is locked")

    def _ensure_unique_name(
        self,
        election_id: str,
        election_type: ElectionType,
        position_name: str,
        *,
        exclude_id: str | None = None,
    ) -> None:
        if not position_name.strip():
            raise ValidationError("Position name is required")

        duplicate = self.position_repository.get_by_name(
            election_id,
            election_type,
            position_name,
            exclude_id=exclude_id,
        )
        if duplicate is not None:
            raise ValidationError("A position with this name already exists for the election type")

    def _to_response(self, position: Position) -> PositionResponse:
        candidate_count = len(self.candidate_repository.list_for_position(position.id))
        return PositionResponse(
            id=position.id,
            election_id=position.election_id,
            position_name=position.position_name,
            election_type=position.election_type,
            winner_count=position.winner_count,
            display_order=position.display_order,
            active=position.active,
            candidate_count=candidate_count,
            created_at=position.created_at,
            updated_at=position.updated_at,
        )

    def _audit(
        self,
        user_id: str | None,
        action: str,
        details: dict | None,
    ) -> None:
        if not user_id:
            return
        self.audit_log_repository.add(
            AuditLog(
                id=new_uuid(),
                user_id=user_id,
                module="Positions",
                action=action,
                new_value=details,
            )
        )
