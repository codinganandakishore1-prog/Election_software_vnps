"""Election management service."""

from __future__ import annotations

from pathlib import Path

from election_platform.enums.election import CandidateStatus, ElectionStatus, ElectionType

from app.database.base import utc_now
from app.database.seeds import new_uuid
from app.exceptions.base import ElectionLockedError, NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.candidate import Candidate
from app.models.election import Election
from app.models.position import Position
from app.models.sync import PublishedConfiguration
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.election_repository import ElectionRepository
from app.repositories.node_repository import PublishedConfigurationRepository
from app.repositories.position_repository import PositionRepository
from app.schemas.election import (
    ElectionCreate,
    ElectionDetailResponse,
    ElectionLockResponse,
    ElectionPublishResponse,
    ElectionSummaryResponse,
    ElectionUpdate,
    ElectionValidationResponse,
    PublishedVersionResponse,
)
from app.services.base import BaseService
from app.services.config_package_service import ConfigPackageService
from app.services.house_service import HouseService


class ElectionService(BaseService):
    """Handles election lifecycle, publishing, and version management."""

    def __init__(
        self,
        election_repository: ElectionRepository,
        position_repository: PositionRepository,
        candidate_repository: CandidateRepository,
        published_configuration_repository: PublishedConfigurationRepository,
        audit_log_repository: AuditLogRepository,
        config_package_service: ConfigPackageService,
        house_service: HouseService,
    ) -> None:
        self.election_repository = election_repository
        self.position_repository = position_repository
        self.candidate_repository = candidate_repository
        self.published_configuration_repository = published_configuration_repository
        self.audit_log_repository = audit_log_repository
        self.config_package_service = config_package_service
        self.house_service = house_service

    def list_elections(
        self,
        *,
        status: ElectionStatus | None = None,
        search: str | None = None,
    ) -> list[ElectionSummaryResponse]:
        elections = self.election_repository.list_filtered(status=status, search=search)
        return [self._to_summary(election) for election in elections]

    def get_election(self, election_id: str) -> ElectionDetailResponse:
        election = self._get_election_or_raise(election_id)
        return self._to_detail(election)

    def create_election(self, payload: ElectionCreate, *, user_id: str | None = None) -> ElectionDetailResponse:
        name = payload.name.strip()
        if not name:
            raise ValidationError("Election name is required")

        if self.election_repository.get_by_name(name) is not None:
            raise ValidationError("An election with this name already exists")

        if payload.start_time and payload.end_time and payload.end_time <= payload.start_time:
            raise ValidationError("End time must be after start time")

        now = utc_now()
        election = Election(
            id=new_uuid(),
            election_name=name,
            academic_year=payload.academic_year.strip() if payload.academic_year else None,
            description=payload.description,
            version=0,
            status=ElectionStatus.DRAFT,
            start_time=payload.start_time,
            end_time=payload.end_time,
            configuration_locked=False,
            created_by=user_id,
            active=True,
            created_at=now,
            updated_at=now,
        )
        self.election_repository.add(election)
        self._audit(user_id, "Election Created", {"election_id": election.id, "name": election.election_name})
        self.election_repository.commit()
        return self._to_detail(election)

    def update_election(
        self,
        election_id: str,
        payload: ElectionUpdate,
        *,
        user_id: str | None = None,
    ) -> ElectionDetailResponse:
        election = self._get_election_or_raise(election_id)
        self._ensure_metadata_editable(election)

        if payload.name is not None:
            cleaned = payload.name.strip()
            if not cleaned:
                raise ValidationError("Election name is required")
            duplicate = self.election_repository.get_by_name(cleaned, exclude_id=election_id)
            if duplicate is not None:
                raise ValidationError("An election with this name already exists")
            election.election_name = cleaned

        if payload.academic_year is not None:
            election.academic_year = payload.academic_year.strip() or None
        if payload.description is not None:
            election.description = payload.description
        if payload.start_time is not None:
            election.start_time = payload.start_time
        if payload.end_time is not None:
            election.end_time = payload.end_time
        if payload.logo_path is not None:
            election.logo_path = payload.logo_path

        if election.start_time and election.end_time and election.end_time <= election.start_time:
            raise ValidationError("End time must be after start time")

        self._audit(user_id, "Election Updated", {"election_id": election.id})
        self.election_repository.commit()
        return self._to_detail(election)

    def delete_election(self, election_id: str, *, user_id: str | None = None) -> None:
        election = self._get_election_or_raise(election_id)

        if election.status in {ElectionStatus.PUBLISHED, ElectionStatus.LIVE, ElectionStatus.COMPLETED}:
            raise ValidationError(f"Cannot delete election while status is {election.status.value}")

        self.election_repository.soft_delete(election)
        self._audit(user_id, "Election Deleted", {"election_id": election_id})
        self.election_repository.commit()

    def validate_election(self, election_id: str) -> ElectionValidationResponse:
        errors = self._collect_validation_errors(election_id)
        return ElectionValidationResponse(valid=not errors, errors=errors)

    def publish_election(self, election_id: str, *, user_id: str | None = None) -> ElectionPublishResponse:
        election = self._get_election_or_raise(election_id)

        if election.status not in {ElectionStatus.DRAFT, ElectionStatus.PUBLISHED}:
            raise ValidationError(f"Cannot publish election with status {election.status.value}")

        errors = self._collect_validation_errors(election_id)
        if errors:
            raise ValidationError("; ".join(errors))

        new_version = election.version + 1
        package = self.config_package_service.build_package(election, new_version)

        published = PublishedConfiguration(
            id=new_uuid(),
            election_id=election.id,
            version=new_version,
            package_path=package.package_path,
            checksum=package.checksum,
            published_at=utc_now(),
            published_by=user_id,
        )
        self.published_configuration_repository.add(published)

        election.version = new_version
        election.status = ElectionStatus.PUBLISHED

        self._mark_candidates_published(election_id)

        self._audit(
            user_id,
            "Election Published",
            {
                "election_id": election.id,
                "version": new_version,
                "checksum": package.checksum,
            },
        )
        self.election_repository.commit()

        return ElectionPublishResponse(
            election_id=election.id,
            version=new_version,
            checksum=package.checksum,
            package_path=package.package_path,
        )

    def lock_election(self, election_id: str, *, user_id: str | None = None) -> ElectionLockResponse:
        election = self._get_election_or_raise(election_id)

        if election.status in {ElectionStatus.LIVE, ElectionStatus.ARCHIVED}:
            raise ValidationError(f"Cannot lock election with status {election.status.value}")

        if election.configuration_locked:
            return ElectionLockResponse(
                election_id=election.id,
                configuration_locked=True,
                status=election.status,
                message="Election configuration is already locked",
            )

        election.configuration_locked = True
        self._audit(user_id, "Election Locked", {"election_id": election.id})
        self.election_repository.commit()

        return ElectionLockResponse(
            election_id=election.id,
            configuration_locked=True,
            status=election.status,
            message="Election configuration locked",
        )

    def unlock_election(self, election_id: str, *, user_id: str | None = None) -> ElectionLockResponse:
        election = self._get_election_or_raise(election_id)

        if election.status == ElectionStatus.LIVE:
            raise ElectionLockedError("Cannot unlock configuration while the election is live")

        if election.status == ElectionStatus.ARCHIVED:
            raise ValidationError("Cannot unlock an archived election")

        if not election.configuration_locked:
            return ElectionLockResponse(
                election_id=election.id,
                configuration_locked=False,
                status=election.status,
                message="Election configuration is already unlocked",
            )

        election.configuration_locked = False
        self._audit(user_id, "Election Unlocked", {"election_id": election.id})
        self.election_repository.commit()

        return ElectionLockResponse(
            election_id=election.id,
            configuration_locked=False,
            status=election.status,
            message="Election configuration unlocked",
        )

    def archive_election(self, election_id: str, *, user_id: str | None = None) -> ElectionDetailResponse:
        election = self._get_election_or_raise(election_id)

        if election.status not in {ElectionStatus.COMPLETED, ElectionStatus.PUBLISHED}:
            raise ValidationError("Only completed or published elections can be archived")

        election.status = ElectionStatus.ARCHIVED
        election.configuration_locked = True
        self._audit(user_id, "Election Archived", {"election_id": election.id})
        self.election_repository.commit()
        return self._to_detail(election)

    def duplicate_election(
        self,
        election_id: str,
        *,
        new_name: str | None = None,
        user_id: str | None = None,
    ) -> ElectionDetailResponse:
        source = self._get_election_or_raise(election_id)

        base_name = (new_name or f"{source.election_name} (Copy)").strip()
        if not base_name:
            raise ValidationError("Election name is required")

        candidate_name = base_name
        suffix = 2
        while self.election_repository.get_by_name(candidate_name) is not None:
            candidate_name = f"{base_name} {suffix}"
            suffix += 1

        now = utc_now()
        new_election = Election(
            id=new_uuid(),
            election_name=candidate_name,
            academic_year=source.academic_year,
            description=source.description,
            version=0,
            status=ElectionStatus.DRAFT,
            start_time=source.start_time,
            end_time=source.end_time,
            logo_path=source.logo_path,
            configuration_locked=False,
            created_by=user_id,
            active=True,
            created_at=now,
            updated_at=now,
        )
        self.election_repository.add(new_election)

        position_map = self._duplicate_positions(source.id, new_election.id)
        self._duplicate_candidates(source.id, new_election.id, position_map)

        self._audit(
            user_id,
            "Election Duplicated",
            {"source_election_id": source.id, "new_election_id": new_election.id},
        )
        self.election_repository.commit()
        return self._to_detail(new_election)

    def list_versions(self, election_id: str) -> list[PublishedVersionResponse]:
        self._get_election_or_raise(election_id)
        versions = self.published_configuration_repository.list_for_election(election_id)
        return [self._to_version_response(record) for record in versions]

    def get_version(self, election_id: str, version: int) -> PublishedVersionResponse:
        self._get_election_or_raise(election_id)
        records = self.published_configuration_repository.list_for_election(election_id)
        for record in records:
            if record.version == version:
                return self._to_version_response(record)
        raise NotFoundError(f"Published version {version} not found")

    def get_latest_configuration(self, election_id: str) -> PublishedVersionResponse | None:
        self._get_election_or_raise(election_id)
        record = self.published_configuration_repository.get_latest_for_election(election_id)
        if record is None:
            return None
        return self._to_version_response(record)

    def start_election(self, election_id: str, *, user_id: str | None = None) -> ElectionDetailResponse:
        election = self._get_election_or_raise(election_id)

        if election.status != ElectionStatus.PUBLISHED:
            raise ValidationError("Only published elections can be started")

        if election.version < 1:
            raise ValidationError("Election must be published before starting")

        election.status = ElectionStatus.LIVE
        election.configuration_locked = True
        self._audit(user_id, "Election Started", {"election_id": election.id})
        self.election_repository.commit()
        return self._to_detail(election)

    def end_election(self, election_id: str, *, user_id: str | None = None) -> ElectionDetailResponse:
        election = self._get_election_or_raise(election_id)

        if election.status != ElectionStatus.LIVE:
            raise ValidationError("Only live elections can be ended")

        election.status = ElectionStatus.COMPLETED
        election.configuration_locked = True
        self._audit(user_id, "Election Ended", {"election_id": election.id})
        self.election_repository.commit()
        return self._to_detail(election)

    def is_configuration_locked(self, election_id: str) -> bool:
        election = self.election_repository.get_by_id(election_id)
        if election is None or election.deleted_at is not None:
            return False
        return election.configuration_locked or election.status in {
            ElectionStatus.LIVE,
            ElectionStatus.COMPLETED,
            ElectionStatus.ARCHIVED,
        }

    def _collect_validation_errors(self, election_id: str) -> list[str]:
        errors: list[str] = []

        election = self.election_repository.get_by_id(election_id)
        if election is None or election.deleted_at is not None:
            return ["Election not found"]

        if not election.election_name.strip():
            errors.append("Election name is required")

        positions = self.position_repository.list_for_election(election_id, include_inactive=False)
        if not positions:
            errors.append("Election must contain at least one position")

        regular_positions = [position for position in positions if position.election_type == ElectionType.REGULAR]
        house_positions = [position for position in positions if position.election_type == ElectionType.HOUSE]

        for position in regular_positions:
            errors.extend(self._validate_position_candidates(position))

        if house_positions:
            house_validation = self.house_service.validate(election_id)
            if not house_validation.valid:
                errors.extend(house_validation.errors)
        elif not regular_positions:
            errors.append("Election must contain at least one regular or house position")

        return errors

    def _validate_position_candidates(self, position: Position) -> list[str]:
        errors: list[str] = []
        candidates = self.candidate_repository.list_for_position(position.id)
        active_candidates = [candidate for candidate in candidates if candidate.deleted_at is None]

        if not active_candidates:
            errors.append(f'Position "{position.position_name}" has no candidates')
            return errors

        for candidate in active_candidates:
            if not candidate.image_id:
                errors.append(
                    f'Candidate "{candidate.candidate_name}" ({position.position_name}) is missing a photo'
                )

        names = [candidate.candidate_name.lower() for candidate in active_candidates]
        if len(names) != len(set(names)):
            errors.append(f'Duplicate candidate names found for position "{position.position_name}"')

        return errors

    def _duplicate_positions(self, source_election_id: str, target_election_id: str) -> dict[str, str]:
        position_map: dict[str, str] = {}
        positions = self.position_repository.list_for_election(source_election_id, include_inactive=False)

        for position in positions:
            new_position = Position(
                id=new_uuid(),
                election_id=target_election_id,
                election_type=position.election_type,
                position_name=position.position_name,
                winner_count=position.winner_count,
                display_order=position.display_order,
                active=True,
            )
            self.position_repository.add(new_position)
            position_map[position.id] = new_position.id

        return position_map

    def _duplicate_candidates(
        self,
        source_election_id: str,
        target_election_id: str,
        position_map: dict[str, str],
    ) -> None:
        candidates = self.candidate_repository.list_for_election(source_election_id)
        for candidate in candidates:
            new_position_id = position_map.get(candidate.position_id)
            if new_position_id is None:
                continue

            self.candidate_repository.add(
                Candidate(
                    id=new_uuid(),
                    election_id=target_election_id,
                    position_id=new_position_id,
                    house_id=candidate.house_id,
                    candidate_name=candidate.candidate_name,
                    display_order=candidate.display_order,
                    image_id=candidate.image_id,
                    status=CandidateStatus.DRAFT,
                    active=True,
                )
            )

    def _mark_candidates_published(self, election_id: str) -> None:
        candidates = self.candidate_repository.list_for_election(election_id)
        for candidate in candidates:
            candidate.status = CandidateStatus.PUBLISHED

    def _get_election_or_raise(self, election_id: str) -> Election:
        election = self.election_repository.get_by_id(election_id)
        if election is None or election.deleted_at is not None:
            raise NotFoundError("Election not found")
        return election

    def _ensure_metadata_editable(self, election: Election) -> None:
        if election.status == ElectionStatus.LIVE:
            raise ElectionLockedError("Cannot modify election while it is live")
        if election.status == ElectionStatus.ARCHIVED:
            raise ValidationError("Cannot modify an archived election")

    def _to_summary(self, election: Election) -> ElectionSummaryResponse:
        positions = self.position_repository.list_for_election(election.id, include_inactive=False)
        candidates = self.candidate_repository.list_for_election(election.id)
        latest = self.published_configuration_repository.get_latest_for_election(election.id)
        published_at = latest.published_at if latest is not None else None

        return ElectionSummaryResponse(
            id=election.id,
            name=election.election_name,
            academic_year=election.academic_year,
            version=election.version,
            status=election.status,
            configuration_locked=election.configuration_locked,
            position_count=len(positions),
            candidate_count=len(candidates),
            published_at=published_at,
            created_at=election.created_at,
            updated_at=election.updated_at,
        )

    def _to_detail(self, election: Election) -> ElectionDetailResponse:
        summary = self._to_summary(election)
        positions = self.position_repository.list_for_election(election.id, include_inactive=False)
        regular_count = sum(1 for position in positions if position.election_type == ElectionType.REGULAR)
        house_count = sum(1 for position in positions if position.election_type == ElectionType.HOUSE)
        latest = self.published_configuration_repository.get_latest_for_election(election.id)
        latest_checksum = latest.checksum if latest is not None else None

        return ElectionDetailResponse(
            **summary.model_dump(),
            description=election.description,
            start_time=election.start_time,
            end_time=election.end_time,
            logo_path=election.logo_path,
            created_by=election.created_by,
            regular_position_count=regular_count,
            house_position_count=house_count,
            latest_checksum=latest_checksum,
        )

    def _to_version_response(self, record: PublishedConfiguration) -> PublishedVersionResponse:
        package_size: int | None = None
        if record.package_path:
            path = Path(record.package_path)
            if path.exists():
                package_size = path.stat().st_size

        return PublishedVersionResponse(
            id=record.id,
            version=record.version,
            checksum=record.checksum,
            package_path=record.package_path,
            published_at=record.published_at,
            published_by=record.published_by,
            package_size=package_size,
        )

    def _audit(self, user_id: str | None, action: str, details: dict | None) -> None:
        if not user_id:
            return
        self.audit_log_repository.add(
            AuditLog(
                id=new_uuid(),
                user_id=user_id,
                module="Elections",
                action=action,
                new_value=details,
            )
        )
