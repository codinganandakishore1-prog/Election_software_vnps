"""Role repository."""

from sqlalchemy.orm import Session

from app.models.user import Role
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """Data access for role records."""

    model = Role

    def get_by_name(self, role_name: str) -> Role | None:
        return self.get_by_field("role_name", role_name)
