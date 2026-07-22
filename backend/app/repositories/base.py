"""Base repository pattern."""

from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.database.base import Base, SoftDeleteMixin, utc_now

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic SQLAlchemy repository with common CRUD operations."""

    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def _base_query(self) -> Select[tuple[ModelT]]:
        return select(self.model)

    def get_by_id(self, record_id: str) -> ModelT | None:
        return self.db.get(self.model, record_id)

    def list_all(self, *, limit: int | None = None, offset: int = 0) -> list[ModelT]:
        stmt = self._base_query().offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())

    def count(self) -> int:
        return self.db.scalar(select(func.count()).select_from(self.model)) or 0

    def add(self, instance: ModelT) -> ModelT:
        self.db.add(instance)
        return instance

    def delete(self, instance: ModelT) -> None:
        self.db.delete(instance)

    def soft_delete(self, instance: ModelT) -> ModelT:
        """Mark a soft-deletable record inactive."""
        if not isinstance(instance, SoftDeleteMixin):
            raise TypeError(f"{self.model.__name__} does not support soft delete")
        instance.active = False
        instance.deleted_at = utc_now()
        return instance

    def flush(self) -> None:
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def get_by_field(self, field_name: str, value: Any) -> ModelT | None:
        column = getattr(self.model, field_name)
        return self.db.scalar(select(self.model).where(column == value))

    def list_by_field(
        self,
        field_name: str,
        value: Any,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[ModelT]:
        column = getattr(self.model, field_name)
        stmt = select(self.model).where(column == value).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())

    def list_active(self, *, limit: int | None = None, offset: int = 0) -> list[ModelT]:
        if not issubclass(self.model, SoftDeleteMixin):
            return self.list_all(limit=limit, offset=offset)
        stmt = (
            select(self.model)
            .where(self.model.active.is_(True), self.model.deleted_at.is_(None))
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())
