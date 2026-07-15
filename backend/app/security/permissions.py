"""Role-based permission checking."""

from election_platform.enums.roles import UserRole


class PermissionChecker:
    """Validate role-based access."""

    @staticmethod
    def has_role(user_role: str, allowed_roles: list[UserRole]) -> bool:
        return any(user_role == role.value for role in allowed_roles)
