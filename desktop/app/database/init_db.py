"""Desktop database initialization helpers."""

from app.database.base import LocalBase
from app.database.session import local_db

import app.models  # noqa: F401


def create_local_tables() -> None:
    """Create all local desktop tables."""
    local_db.create_tables()


def initialize_local_database() -> None:
    """Bootstrap the local SQLite/MySQL schema for a voting node."""
    create_local_tables()
