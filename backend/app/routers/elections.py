"""Election management router."""

from election_platform.enums.admin import NotificationType
from election_platform.enums.election import ElectionStatus
from election_platform.enums.roles import UserRole
from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.providers import ServiceContainer
from app.schemas.election import (
    ElectionCreate,
    ElectionDetailResponse,
    ElectionDuplicateRequest,
    ElectionLockResponse,
    ElectionPublishResponse,
    ElectionSummaryResponse,
    ElectionUpdate,
    ElectionValidationResponse,
    PublishedVersionResponse,
)
from app.websocket.broadcaster import broadcast_election_status

router = APIRouter()

AdminUser = Depends(require_roles(UserRole.SUPER_ADMINISTRATOR, UserRole.ADMINISTRATOR))


@router.get("")
async def list_elections(
    current_user: CurrentUser,
    container: ServiceContainer,
    status: ElectionStatus | None = Query(default=None),
    search: str | None = Query(default=None),
) -> APIResponse[list[ElectionSummaryResponse]]:
    """List all elections."""
    _ = current_user
    elections = container.election_service.list_elections(status=status, search=search)
    return APIResponse.ok(data=elections)


@router.get("/{election_id}")
async def get_election(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[ElectionDetailResponse]:
    """Get election details."""
    _ = current_user
    election = container.election_service.get_election(election_id)
    return APIResponse.ok(data=election)


@router.post("")
async def create_election(
    payload: ElectionCreate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[ElectionDetailResponse]:
    """Create a new election."""
    election = container.election_service.create_election(payload, user_id=current_user.id)
    return APIResponse.ok(message="Election created successfully", data=election)


@router.put("/{election_id}")
async def update_election(
    election_id: str,
    payload: ElectionUpdate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[ElectionDetailResponse]:
    """Update election metadata."""
    election = container.election_service.update_election(election_id, payload, user_id=current_user.id)
    return APIResponse.ok(message="Election updated successfully", data=election)


@router.delete("/{election_id}")
async def delete_election(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[None]:
    """Soft delete an election."""
    container.election_service.delete_election(election_id, user_id=current_user.id)
    return APIResponse.ok(message="Election deleted successfully")


@router.get("/{election_id}/validate")
async def validate_election(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[ElectionValidationResponse]:
    """Validate election readiness for publishing."""
    _ = current_user
    result = container.election_service.validate_election(election_id)
    return APIResponse.ok(data=result)


@router.post("/{election_id}/publish")
async def publish_election(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[ElectionPublishResponse]:
    """Publish election configuration."""
    result = container.election_service.publish_election(election_id, user_id=current_user.id)
    election = container.election_repository.get_by_id(election_id)
    election_name = election.election_name if election else election_id
    await container.notification_service.create_and_broadcast(
        title="Election published",
        message=f'"{election_name}" configuration v{result.version} has been published.',
        notification_type=NotificationType.ELECTION_PUBLISHED.value,
    )
    await broadcast_election_status(
        election_id=election_id,
        election_name=election_name,
        status=ElectionStatus.PUBLISHED.value,
    )
    return APIResponse.ok(message="Election published successfully", data=result)


@router.post("/{election_id}/lock")
async def lock_election(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[ElectionLockResponse]:
    """Lock election configuration from further edits."""
    result = container.election_service.lock_election(election_id, user_id=current_user.id)
    return APIResponse.ok(message=result.message, data=result)


@router.post("/{election_id}/unlock")
async def unlock_election(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[ElectionLockResponse]:
    """Unlock election configuration for editing."""
    result = container.election_service.unlock_election(election_id, user_id=current_user.id)
    return APIResponse.ok(message=result.message, data=result)


@router.post("/{election_id}/archive")
async def archive_election(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[ElectionDetailResponse]:
    """Archive an election."""
    election = container.election_service.archive_election(election_id, user_id=current_user.id)
    return APIResponse.ok(message="Election archived successfully", data=election)


@router.post("/{election_id}/duplicate")
async def duplicate_election(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    payload: ElectionDuplicateRequest | None = None,
    _: None = AdminUser,
) -> APIResponse[ElectionDetailResponse]:
    """Duplicate an election as a new draft."""
    new_name = payload.name if payload else None
    election = container.election_service.duplicate_election(
        election_id,
        new_name=new_name,
        user_id=current_user.id,
    )
    return APIResponse.ok(message="Election duplicated successfully", data=election)


@router.get("/{election_id}/versions")
async def list_election_versions(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[list[PublishedVersionResponse]]:
    """List published configuration versions."""
    _ = current_user
    versions = container.election_service.list_versions(election_id)
    return APIResponse.ok(data=versions)


@router.get("/{election_id}/versions/{version}")
async def get_election_version(
    election_id: str,
    version: int,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[PublishedVersionResponse]:
    """Get metadata for a specific published version."""
    _ = current_user
    record = container.election_service.get_version(election_id, version)
    return APIResponse.ok(data=record)


@router.get("/{election_id}/configuration")
async def get_election_configuration(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[PublishedVersionResponse | None]:
    """Return latest published configuration metadata."""
    _ = current_user
    record = container.election_service.get_latest_configuration(election_id)
    return APIResponse.ok(data=record)


@router.post("/{election_id}/start")
async def start_election(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[ElectionDetailResponse]:
    """Start live voting."""
    election = container.election_service.start_election(election_id, user_id=current_user.id)
    await container.notification_service.create_and_broadcast(
        title="Election started",
        message=f'"{election.name}" is now live.',
        notification_type=NotificationType.ELECTION_STARTED.value,
    )
    await broadcast_election_status(
        election_id=election.id,
        election_name=election.name,
        status=ElectionStatus.LIVE.value,
    )
    return APIResponse.ok(message="Election started successfully", data=election)


@router.post("/{election_id}/pause")
async def pause_election(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[ElectionDetailResponse]:
    """Pause a live election without ending it."""
    election = container.election_service.pause_election(election_id, user_id=current_user.id)
    await container.notification_service.create_and_broadcast(
        title="Election paused",
        message=f'"{election.name}" voting is paused.',
        notification_type=NotificationType.ELECTION_PAUSED.value,
    )
    await broadcast_election_status(
        election_id=election.id,
        election_name=election.name,
        status=ElectionStatus.PAUSED.value,
    )
    return APIResponse.ok(message="Election paused successfully", data=election)


@router.post("/{election_id}/resume")
async def resume_election(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[ElectionDetailResponse]:
    """Resume a paused election."""
    election = container.election_service.resume_election(election_id, user_id=current_user.id)
    await container.notification_service.create_and_broadcast(
        title="Election resumed",
        message=f'"{election.name}" voting is live again.',
        notification_type=NotificationType.ELECTION_RESUMED.value,
    )
    await broadcast_election_status(
        election_id=election.id,
        election_name=election.name,
        status=ElectionStatus.LIVE.value,
    )
    return APIResponse.ok(message="Election resumed successfully", data=election)


@router.post("/{election_id}/end")
async def end_election(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[ElectionDetailResponse]:
    """End live voting."""
    election = container.election_service.end_election(election_id, user_id=current_user.id)
    await container.notification_service.create_and_broadcast(
        title="Election ended",
        message=f'"{election.name}" voting has ended.',
        notification_type=NotificationType.ELECTION_ENDED.value,
    )
    await broadcast_election_status(
        election_id=election.id,
        election_name=election.name,
        status=ElectionStatus.COMPLETED.value,
    )
    return APIResponse.ok(message="Election ended successfully", data=election)
