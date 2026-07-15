"""Candidate management service."""

from __future__ import annotations

from election_platform.enums.election import CandidateStatus, ElectionStatus, ElectionType

from app.database.seeds import new_uuid
from app.exceptions.base import ElectionLockedError, NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.candidate import Candidate
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.election_repository import ElectionRepository
from app.repositories.house_repository import HouseRepository
from app.repositories.position_repository import PositionRepository
from app.schemas.candidate import CandidateCreate, CandidateResponse, CandidateUpdate
from app.schemas.house import HouseCandidateCreate, HouseCandidateResponse, HouseCandidateUpdate
from app.services.base import BaseService


class CandidateService(BaseService):
    """Handles candidate CRUD with house election validation."""

    def __init__(
        self,
        candidate_repository: CandidateRepository,
        position_repository: PositionRepository,
        election_repository: ElectionRepository,
        house_repository: HouseRepository,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        self.candidate_repository = candidate_repository
        self.position_repository = position_repository
        self.election_repository = election_repository
        self.house_repository = house_repository
        self.audit_log_repository = audit_log_repository

    def list_candidates(
        self,
        *,
        election_id: str | None = None,
        election_type: ElectionType | None = None,
        house_id: str | None = None,
        search: str | None = None,
    ) -> list[CandidateResponse]:
        if election_id and election_type is not None:
            candidates = self.candidate_repository.list_for_election_type(election_id, election_type)
        elif election_id:
            candidates = self.candidate_repository.list_for_election(election_id)
        elif search:
            candidates = self.candidate_repository.search_by_name(search, election_id=election_id)
        else:
            candidates = self.candidate_repository.list_active()

        if house_id is not None:
            candidates = [candidate for candidate in candidates if candidate.house_id == house_id]

        return [self._to_response(candidate) for candidate in candidates]

    def get_candidate(self, candidate_id: str) -> CandidateResponse:
        candidate = self._get_candidate_or_raise(candidate_id)
        return self._to_response(candidate)

    def create_candidate(self, payload: CandidateCreate, *, user_id: str | None = None) -> CandidateResponse:
        position = self._get_position_or_raise(payload.position_id)
        self._ensure_election_editable(payload.election_id)
        self._validate_house_assignment(position.election_type, payload.house_id)
        self._ensure_unique_name(payload.position_id, payload.candidate_name, house_id=payload.house_id)

        candidate = Candidate(
            id=new_uuid(),
            election_id=payload.election_id,
            position_id=payload.position_id,
            house_id=payload.house_id,
            candidate_name=payload.candidate_name.strip(),
            candidate_class=(payload.candidate_class or "").strip() or None,
            candidate_section=(payload.candidate_section or "").strip() or None,
            display_order=payload.display_order,
            status=CandidateStatus.DRAFT,
        )
        self.candidate_repository.add(candidate)
        self._audit(
            user_id,
            "Candidate Created",
            {"candidate_id": candidate.id, "candidate_name": candidate.candidate_name},
        )
        self.candidate_repository.commit()
        candidate = self._get_candidate_or_raise(candidate.id)
        return self._to_response(candidate)

    def create_house_candidate(
        self,
        payload: HouseCandidateCreate,
        *,
        user_id: str | None = None,
    ) -> HouseCandidateResponse:
        position = self._get_position_or_raise(payload.position_id)
        if position.election_type != ElectionType.HOUSE:
            raise ValidationError("Position must belong to the House election")
        if position.election_id != payload.election_id:
            raise ValidationError("Position does not belong to the selected election")

        house = self.house_repository.get_by_id(payload.house_id)
        if house is None or not house.active:
            raise NotFoundError("House not found")

        response = self.create_candidate(
            CandidateCreate(
                election_id=payload.election_id,
                candidate_name=payload.candidate_name,
                position_id=payload.position_id,
                house_id=payload.house_id,
                candidate_class=payload.candidate_class,
                candidate_section=payload.candidate_section,
                display_order=payload.display_order,
            ),
            user_id=user_id,
        )
        candidate = self._get_candidate_or_raise(response.id)
        return self._to_house_candidate_response(candidate)

    def update_candidate(
        self,
        candidate_id: str,
        payload: CandidateUpdate,
        *,
        user_id: str | None = None,
    ) -> CandidateResponse:
        candidate = self._get_candidate_or_raise(candidate_id)
        self._ensure_election_editable(candidate.election_id)

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise ValidationError("No fields provided to update")

        position = candidate.position
        if "position_id" in updates:
            position = self._get_position_or_raise(updates["position_id"])

        target_house_id = updates.get("house_id", candidate.house_id)
        self._validate_house_assignment(position.election_type, target_house_id)

        if "candidate_name" in updates:
            new_name = updates["candidate_name"].strip()
            self._ensure_unique_name(
                position.id,
                new_name,
                house_id=target_house_id,
                exclude_id=candidate.id,
            )
            candidate.candidate_name = new_name

        if "position_id" in updates:
            candidate.position_id = updates["position_id"]
        if "house_id" in updates:
            candidate.house_id = updates["house_id"]
        if "candidate_class" in updates:
            value = updates["candidate_class"]
            candidate.candidate_class = (value or "").strip() or None if value is not None else None
        if "candidate_section" in updates:
            value = updates["candidate_section"]
            candidate.candidate_section = (value or "").strip() or None if value is not None else None
        if "display_order" in updates:
            candidate.display_order = updates["display_order"]

        self._audit(user_id, "Candidate Updated", {"candidate_id": candidate.id, **updates})
        self.candidate_repository.commit()
        return self._to_response(candidate)

    def update_house_candidate(
        self,
        candidate_id: str,
        payload: HouseCandidateUpdate,
        *,
        user_id: str | None = None,
    ) -> HouseCandidateResponse:
        response = self.update_candidate(
            candidate_id,
            CandidateUpdate(**payload.model_dump(exclude_unset=True)),
            user_id=user_id,
        )
        candidate = self._get_candidate_or_raise(response.id)
        return self._to_house_candidate_response(candidate)

    def delete_candidate(self, candidate_id: str, *, user_id: str | None = None) -> None:
        candidate = self._get_candidate_or_raise(candidate_id)
        self._ensure_election_editable(candidate.election_id)
        self.candidate_repository.soft_delete(candidate)
        self._audit(
            user_id,
            "Candidate Deleted",
            {"candidate_id": candidate.id, "candidate_name": candidate.candidate_name},
        )
        self.candidate_repository.commit()

    def _get_candidate_or_raise(self, candidate_id: str) -> Candidate:
        candidate = self.candidate_repository.get_by_id(candidate_id)
        if candidate is None or candidate.deleted_at is not None:
            raise NotFoundError("Candidate not found")
        return candidate

    def _get_position_or_raise(self, position_id: str):
        position = self.position_repository.get_by_id(position_id)
        if position is None or position.deleted_at is not None:
            raise NotFoundError("Position not found")
        return position

    def _ensure_election_editable(self, election_id: str) -> None:
        election = self.election_repository.get_by_id(election_id)
        if election is None or election.deleted_at is not None:
            raise NotFoundError("Election not found")
        if election.status == ElectionStatus.LIVE:
            raise ElectionLockedError("Cannot modify candidates while the election is live")
        if election.configuration_locked is True:
            raise ElectionLockedError("Election configuration is locked")

    def _validate_house_assignment(self, election_type: ElectionType, house_id: str | None) -> None:
        if election_type == ElectionType.HOUSE:
            if not house_id:
                raise ValidationError("House is required for House Election candidates")
            house = self.house_repository.get_by_id(house_id)
            if house is None or not house.active:
                raise NotFoundError("House not found")
        elif house_id is not None:
            raise ValidationError("Regular election candidates must not have a house assignment")

    def _ensure_unique_name(
        self,
        position_id: str,
        candidate_name: str,
        *,
        house_id: str | None = None,
        exclude_id: str | None = None,
    ) -> None:
        if not candidate_name.strip():
            raise ValidationError("Candidate name is required")

        duplicate = self.candidate_repository.get_duplicate_name(
            position_id,
            candidate_name,
            house_id=house_id,
            exclude_id=exclude_id,
        )
        if duplicate is not None:
            raise ValidationError("A candidate with this name already exists for the position")

    def _to_response(self, candidate: Candidate) -> CandidateResponse:
        return CandidateResponse(
            id=candidate.id,
            election_id=candidate.election_id,
            candidate_name=candidate.candidate_name,
            position_id=candidate.position_id,
            position_name=candidate.position.position_name,
            house_id=candidate.house_id,
            house_name=candidate.house.house_name if candidate.house else None,
            election_type=candidate.position.election_type.value,
            candidate_class=candidate.candidate_class,
            candidate_section=candidate.candidate_section,
            display_order=candidate.display_order,
            status=candidate.status.value,
            has_image=candidate.image_id is not None,
            image_id=candidate.image_id,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at,
        )

    def _to_house_candidate_response(self, candidate: Candidate) -> HouseCandidateResponse:
        return HouseCandidateResponse(
            id=candidate.id,
            election_id=candidate.election_id,
            position_id=candidate.position_id,
            position_name=candidate.position.position_name,
            house_id=candidate.house_id or "",
            house_name=candidate.house.house_name if candidate.house else "",
            candidate_name=candidate.candidate_name,
            candidate_class=candidate.candidate_class,
            candidate_section=candidate.candidate_section,
            display_order=candidate.display_order,
            status=candidate.status.value,
            has_image=candidate.image_id is not None,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at,
        )

    def _audit(self, user_id: str | None, action: str, details: dict | None) -> None:
        if not user_id:
            return
        self.audit_log_repository.add(
            AuditLog(
                id=new_uuid(),
                user_id=user_id,
                module="Candidates",
                action=action,
                new_value=details,
            )
        )
