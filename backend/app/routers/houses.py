"""House management router."""

from election_platform.enums.roles import UserRole
from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.providers import ServiceContainer
from app.schemas.house import (
    HouseCandidateCreate,
    HouseCandidateResponse,
    HouseCandidateUpdate,
    HouseConfigurationRequest,
    HouseConfigurationResponse,
    HouseResponse,
    HouseValidationResponse,
)

router = APIRouter()

AdminUser = Depends(require_roles(UserRole.SUPER_ADMINISTRATOR, UserRole.ADMINISTRATOR))


@router.get("")
async def list_houses(
    current_user: CurrentUser,
    container: ServiceContainer,
    details: bool = Query(default=False),
) -> APIResponse[list[str] | list[HouseResponse]]:
    """Return house names (SRS) or full records when details=true."""
    _ = current_user
    if details:
        return APIResponse.ok(data=container.house_service.list_houses())
    return APIResponse.ok(data=container.house_service.list_house_names())


@router.get("/configuration")
async def get_house_configuration(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[HouseConfigurationResponse]:
    """Return house positions and candidate coverage for an election."""
    _ = current_user
    configuration = container.house_service.get_configuration(election_id)
    return APIResponse.ok(data=configuration)


@router.put("/configuration")
async def configure_houses(
    payload: HouseConfigurationRequest,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[HouseConfigurationResponse]:
    """Configure shared house leadership positions for all four houses."""
    configuration = container.house_service.configure_positions(payload, user_id=current_user.id)
    return APIResponse.ok(message="House configuration saved successfully", data=configuration)


@router.get("/validate")
async def validate_house_configuration(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[HouseValidationResponse]:
    """Validate house configuration, candidates, and node assignments."""
    _ = current_user
    result = container.house_service.validate(election_id)
    return APIResponse.ok(data=result)


@router.get("/candidates")
async def list_house_candidates(
    election_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    house_id: str | None = Query(default=None),
) -> APIResponse[list[HouseCandidateResponse]]:
    """List house election candidates."""
    _ = current_user
    candidates = container.house_service.list_house_candidates(election_id, house_id=house_id)
    return APIResponse.ok(data=candidates)


@router.post("/candidates")
async def create_house_candidate(
    payload: HouseCandidateCreate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[HouseCandidateResponse]:
    """Create a house election candidate."""
    candidate = container.candidate_service.create_house_candidate(payload, user_id=current_user.id)
    return APIResponse.ok(message="House candidate created successfully", data=candidate)


@router.put("/candidates/{candidate_id}")
async def update_house_candidate(
    candidate_id: str,
    payload: HouseCandidateUpdate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[HouseCandidateResponse]:
    """Update a house election candidate."""
    candidate = container.candidate_service.update_house_candidate(
        candidate_id,
        payload,
        user_id=current_user.id,
    )
    return APIResponse.ok(message="House candidate updated successfully", data=candidate)


@router.delete("/candidates/{candidate_id}")
async def delete_house_candidate(
    candidate_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[None]:
    """Delete a house election candidate."""
    container.candidate_service.delete_candidate(candidate_id, user_id=current_user.id)
    return APIResponse.ok(message="House candidate deleted successfully")
