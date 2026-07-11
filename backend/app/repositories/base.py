"""Base repository pattern."""

from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic SQLAlchemy repository."""

    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, record_id: str) -> ModelT | None:
        return self.db.get(self.model, record_id)

    def list_all(self) -> list[ModelT]:
        return list(self.db.query(self.model).all())

    def add(self, instance: ModelT) -> ModelT:
        self.db.add(instance)
        return instance

    def delete(self, instance: ModelT) -> None:
        self.db.delete(instance)

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
