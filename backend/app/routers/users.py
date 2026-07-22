"""User management router."""

from election_platform.enums.roles import UserRole
from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, Depends

from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.providers import ServiceContainer
from app.schemas.auth import AuthenticatedUserResponse
from app.schemas.user import (
    UserCreate,
    UserPasswordChange,
    UserPasswordReset,
    UserProfileUpdate,
    UserResponse,
    UserUpdate,
)

router = APIRouter()

AdminUser = Depends(require_roles(UserRole.SUPER_ADMINISTRATOR, UserRole.ADMINISTRATOR))
SuperAdminUser = Depends(require_roles(UserRole.SUPER_ADMINISTRATOR))


@router.get("/me")
async def get_current_user_profile(
    current_user: CurrentUser,
) -> APIResponse[AuthenticatedUserResponse]:
    """Return current authenticated user."""
    return APIResponse.ok(
        data=AuthenticatedUserResponse(
            id=current_user.id,
            username=current_user.username,
            full_name=current_user.full_name,
            email=current_user.email,
            role=current_user.role.role_name if current_user.role else "",
        )
    )


@router.put("/me")
async def update_current_user_profile(
    payload: UserProfileUpdate,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[AuthenticatedUserResponse]:
    """Update the signed-in user's profile."""
    user = container.user_service.update_own_profile(
        current_user.id,
        payload,
        actor_id=current_user.id,
    )
    return APIResponse.ok(
        message="Profile updated successfully",
        data=AuthenticatedUserResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
        ),
    )


@router.patch("/change-password")
async def change_password(
    payload: UserPasswordChange,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[None]:
    """Change the signed-in user's password."""
    container.user_service.change_password(current_user.id, payload)
    return APIResponse.ok(message="Password changed successfully")


@router.get("")
async def list_users(
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[list[UserResponse]]:
    """List all users."""
    _ = current_user
    users = container.user_service.list_users()
    return APIResponse.ok(data=users)


@router.post("")
async def create_user(
    payload: UserCreate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = SuperAdminUser,
) -> APIResponse[UserResponse]:
    """Create a new user."""
    user = container.user_service.create_user(payload, actor_id=current_user.id)
    return APIResponse.ok(message="User created successfully", data=user)


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    payload: UserUpdate,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = SuperAdminUser,
) -> APIResponse[UserResponse]:
    """Update an existing user."""
    user = container.user_service.update_user(user_id, payload, actor_id=current_user.id)
    return APIResponse.ok(message="User updated successfully", data=user)


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    payload: UserPasswordReset,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = SuperAdminUser,
) -> APIResponse[None]:
    """Reset a user's password."""
    container.user_service.reset_password(user_id, payload, actor_id=current_user.id)
    return APIResponse.ok(message="Password reset successfully")


@router.post("/{user_id}/disable")
async def disable_user(
    user_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = SuperAdminUser,
) -> APIResponse[UserResponse]:
    """Disable a user account."""
    user = container.user_service.disable_user(user_id, actor_id=current_user.id)
    return APIResponse.ok(message="User disabled successfully", data=user)
