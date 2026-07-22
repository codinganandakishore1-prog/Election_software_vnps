"""Desktop repository base."""

from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.database.base import LocalBase

ModelT = TypeVar("ModelT", bound=LocalBase)


class LocalBaseRepository(Generic[ModelT]):
    """Generic SQLAlchemy repository for desktop local models."""

    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, record_id: str) -> ModelT | None:
        return self.db.get(self.model, record_id)

    def list_all(self, *, limit: int | None = None, offset: int = 0) -> list[ModelT]:
        stmt = select(self.model).offset(offset)
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

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def flush(self) -> None:
        self.db.flush()
