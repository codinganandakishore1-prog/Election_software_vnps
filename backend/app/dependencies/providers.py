"""FastAPI dependency providers."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.container import Container, get_container

DbSession = Annotated[Session, Depends(get_db)]


def get_service_container(db: DbSession) -> Generator[Container, None, None]:
    """Provide a service container for the current request."""
    yield get_container(db)


ServiceContainer = Annotated[Container, Depends(get_service_container)]
