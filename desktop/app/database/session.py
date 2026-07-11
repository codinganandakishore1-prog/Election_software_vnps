"""Local database session management (placeholder)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from desktop.app.config.settings import settings


class LocalDatabase:
    """Manage local MySQL/SQLite connection for offline voting."""

    def __init__(self) -> None:
        self._engine = None
        self._session_factory: sessionmaker[Session] | None = None

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{settings.local_db_user}:{settings.local_db_password}"
            f"@{settings.local_db_host}:{settings.local_db_port}/{settings.local_db_name}"
        )

    def connect(self) -> sessionmaker[Session]:
        if self._session_factory is None:
            self._engine = create_engine(self.database_url, pool_pre_ping=True)
            self._session_factory = sessionmaker(bind=self._engine, autocommit=False, autoflush=False)
        return self._session_factory

    # Implementation deferred to database phase.
