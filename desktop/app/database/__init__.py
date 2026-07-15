"""Desktop database package."""

from app.database.base import LocalBase, UUIDPrimaryKeyMixin, utc_now
from app.database.init_db import create_local_tables, initialize_local_database
from app.database.session import LocalDatabase, get_local_db, local_db

__all__ = [
    "LocalBase",
    "LocalDatabase",
    "UUIDPrimaryKeyMixin",
    "create_local_tables",
    "get_local_db",
    "initialize_local_database",
    "local_db",
    "utc_now",
]
