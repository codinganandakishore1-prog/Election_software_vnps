"""Local database session management."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings
from app.database.base import LocalBase


class LocalDatabase:
    """Manage local SQLite/MySQL connection for offline voting."""

    def __init__(self) -> None:
        self._engine = None
        self._session_factory: sessionmaker[Session] | None = None

    @property
    def database_url(self) -> str:
        return settings.local_database_url

    @property
    def engine(self):
        if self._engine is None:
            connect_args = {}
            if settings.local_db_engine.lower() == "sqlite":
                connect_args["check_same_thread"] = False
            self._engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                connect_args=connect_args,
            )
        return self._engine

    def connect(self) -> sessionmaker[Session]:
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
            )
        return self._session_factory

    def create_tables(self) -> None:
        """Create all local tables (development/bootstrap)."""
        import app.models  # noqa: F401

        LocalBase.metadata.create_all(bind=self.engine)

    def dispose(self) -> None:
        """Dispose engine and reset session factory."""
        if self._engine is not None:
            self._engine.dispose()
        self._engine = None
        self._session_factory = None

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around local DB operations."""
        factory = self.connect()
        session = factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


local_db = LocalDatabase()


def get_local_db() -> Generator[Session, None, None]:
    """Yield a local database session."""
    factory = local_db.connect()
    session = factory()
    try:
        yield session
    finally:
        session.close()
