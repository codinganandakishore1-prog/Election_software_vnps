"""Candidate management router."""

from election_platform.enums.election import ElectionType
from election_platform.enums.roles import UserRole
from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.providers import ServiceContainer
from app.schemas.candidate import CandidateCreate, CandidateResponse, CandidateUpdate
from app.schemas.image import ImageUploadResponse

router = APIRouter()

AdminUser = Depends(require_roles(UserRole.SUPER_ADMINISTRATOR, UserRole.ADMINISTRATOR))


@router.get("")
async def list_candidates(
    current_user: CurrentUser,
    container: ServiceContainer,
    election_id: str | None = Query(default=None),
    election_type: ElectionType | None = Query(default=None),
    house_id: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> APIResponse[list[CandidateResponse]]:
    """List candidates with optional filters."""
    _ = current_user
    candidates = container.candidate_service.list_candidates(
        election_id=election_id,
        election_type=election_type,
        house_id=house_id,
        search=search,
    )
    return APIResponse.ok(data=candidates)


@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[CandidateResponse]:
    """Get candidate details."""
    _ = current_user
    candidate = container.candidate_service.get_candidate(candidate_id)
    return APIResponse.ok(data=candidate)


@router.post("")
async def create_candidate(
    payload: CandidateCreate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[CandidateResponse]:
    """Create a new candidate."""
    candidate = container.candidate_service.create_candidate(payload, user_id=current_user.id)
    return APIResponse.ok(message="Candidate created successfully", data=candidate)


@router.put("/{candidate_id}")
async def update_candidate(
    candidate_id: str,
    payload: CandidateUpdate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[CandidateResponse]:
    """Update candidate details."""
    candidate = container.candidate_service.update_candidate(candidate_id, payload, user_id=current_user.id)
    return APIResponse.ok(message="Candidate updated successfully", data=candidate)


@router.delete("/{candidate_id}")
async def delete_candidate(
    candidate_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[None]:
    """Delete a candidate."""
    container.candidate_service.delete_candidate(candidate_id, user_id=current_user.id)
    return APIResponse.ok(message="Candidate deleted successfully")


@router.post("/{candidate_id}/image")
async def upload_candidate_image(
    candidate_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    file: UploadFile = File(...),
) -> APIResponse[ImageUploadResponse]:
    """Upload a candidate image."""
    result = await container.image_service.upload_for_candidate(
        candidate_id,
        file,
        user_id=current_user.id,
        replace=False,
    )
    return APIResponse.ok(message="Image uploaded successfully", data=result)


@router.put("/{candidate_id}/image")
async def replace_candidate_image(
    candidate_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    file: UploadFile = File(...),
) -> APIResponse[ImageUploadResponse]:
    """Replace an existing candidate image."""
    result = await container.image_service.upload_for_candidate(
        candidate_id,
        file,
        user_id=current_user.id,
        replace=True,
    )
    return APIResponse.ok(message="Image replaced successfully", data=result)
