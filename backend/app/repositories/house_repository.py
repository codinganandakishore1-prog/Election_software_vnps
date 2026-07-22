"""House repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.house import House
from app.repositories.base import BaseRepository


class HouseRepository(BaseRepository[House]):
    """Data access for house records."""

    model = House

    def get_by_name(self, house_name: str) -> House | None:
        return self.get_by_field("house_name", house_name)

    def list_active(self, *, limit: int | None = None, offset: int = 0) -> list[House]:
        return self.list_by_field("active", True, limit=limit, offset=offset)

    def list_all_ordered(self) -> list[House]:
        stmt = select(House).where(House.active.is_(True)).order_by(House.house_name)
        return list(self.db.scalars(stmt).all())
