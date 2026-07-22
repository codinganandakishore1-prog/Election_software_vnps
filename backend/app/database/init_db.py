"""Database initialization helpers."""

from sqlalchemy.engine import Engine

from app.database.base import Base
from app.database.seeds import seed_database
from app.database.session import SessionLocal, engine, session_scope

# Import all models so metadata is fully populated.
import app.models  # noqa: F401


def create_tables(bind: Engine | None = None) -> None:
    """Create all tables from SQLAlchemy metadata."""
    Base.metadata.create_all(bind=bind or engine)


def initialize_database(*, seed: bool = True, bind: Engine | None = None) -> dict[str, int] | None:
    """
    Create schema and optionally seed default master data.

    Prefer Alembic migrations in production; this is intended for
    development bootstrap and tests.
    """
    create_tables(bind=bind)
    if not seed:
        return None

    with session_scope() as db:
        return seed_database(db)


def get_session_factory():
    """Return the configured session factory."""
    return SessionLocal
