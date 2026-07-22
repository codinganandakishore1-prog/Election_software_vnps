"""Position management router."""

from election_platform.enums.election import ElectionType
from election_platform.enums.roles import UserRole
from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.providers import ServiceContainer
from app.schemas.position import (
    PositionCreate,
    PositionReorderRequest,
    PositionResponse,
    PositionUpdate,
)

router = APIRouter()

AdminUser = Depends(require_roles(UserRole.SUPER_ADMINISTRATOR, UserRole.ADMINISTRATOR))


@router.get("")
async def list_positions(
    current_user: CurrentUser,
    container: ServiceContainer,
    election_id: str | None = Query(default=None),
    election_type: ElectionType | None = Query(default=None),
    search: str | None = Query(default=None),
    active: bool | None = Query(default=None),
) -> APIResponse[list[PositionResponse]]:
    """List positions with optional filters."""
    _ = current_user
    positions = container.position_service.list_positions(
        election_id=election_id,
        election_type=election_type,
        search=search,
        active=active,
    )
    return APIResponse.ok(data=positions)


@router.post("")
async def create_position(
    payload: PositionCreate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[PositionResponse]:
    """Create a new position."""
    position = container.position_service.create_position(payload, user_id=current_user.id)
    return APIResponse.ok(message="Position created successfully", data=position)


@router.put("/reorder")
async def reorder_positions(
    payload: PositionReorderRequest,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[list[PositionResponse]]:
    """Reorder positions for an election type."""
    positions = container.position_service.reorder_positions(payload, user_id=current_user.id)
    return APIResponse.ok(message="Positions reordered successfully", data=positions)


@router.get("/{position_id}")
async def get_position(
    position_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[PositionResponse]:
    """Get a single position."""
    _ = current_user
    position = container.position_service.get_position(position_id)
    return APIResponse.ok(data=position)


@router.put("/{position_id}")
async def update_position(
    position_id: str,
    payload: PositionUpdate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[PositionResponse]:
    """Update position details."""
    position = container.position_service.update_position(position_id, payload, user_id=current_user.id)
    return APIResponse.ok(message="Position updated successfully", data=position)


@router.delete("/{position_id}")
async def delete_position(
    position_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[None]:
    """Delete a position."""
    container.position_service.delete_position(position_id, user_id=current_user.id)
    return APIResponse.ok(message="Position deleted successfully")


@router.post("/{position_id}/enable")
async def enable_position(
    position_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[PositionResponse]:
    """Enable a position."""
    position = container.position_service.enable_position(position_id, user_id=current_user.id)
    return APIResponse.ok(message="Position enabled successfully", data=position)


@router.post("/{position_id}/disable")
async def disable_position(
    position_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[PositionResponse]:
    """Disable a position."""
    position = container.position_service.disable_position(position_id, user_id=current_user.id)
    return APIResponse.ok(message="Position disabled successfully", data=position)


@router.post("/{position_id}/move-up")
async def move_position_up(
    position_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[PositionResponse]:
    """Move a position up in display order."""
    position = container.position_service.move_position(position_id, "up", user_id=current_user.id)
    return APIResponse.ok(message="Position moved up", data=position)


@router.post("/{position_id}/move-down")
async def move_position_down(
    position_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[PositionResponse]:
    """Move a position down in display order."""
    position = container.position_service.move_position(position_id, "down", user_id=current_user.id)
    return APIResponse.ok(message="Position moved down", data=position)
