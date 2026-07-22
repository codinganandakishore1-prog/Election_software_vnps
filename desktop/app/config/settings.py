"""Desktop application configuration."""

from functools import lru_cache
from pathlib import Path

from election_platform.config.base import BaseAppSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from app.runtime_paths import data_root, is_frozen, resource_root

_DATA_ROOT = data_root()
_RESOURCE_ROOT = resource_root()


def _env_files() -> tuple[Path, ...]:
    """Load .env next to the EXE when frozen; also repo-root .env in source runs."""
    paths: list[Path] = [_DATA_ROOT / ".env"]
    if not is_frozen():
        # desktop/ → repo root (useful when developing from a full checkout)
        paths.append(_RESOURCE_ROOT.parent / ".env")
    return tuple(paths)


class DesktopSettings(BaseAppSettings):
    """Desktop-specific settings."""

    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    website_url: str = Field(default="http://localhost:8000", alias="WEBSITE_URL")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    node_id: str = Field(default="", alias="NODE_ID")
    node_secret: str = Field(default="", alias="NODE_SECRET")
    config_dir: Path = Field(default=_DATA_ROOT / "data" / "config", alias="DESKTOP_CONFIG_DIR")
    log_dir: Path = Field(default=_DATA_ROOT / "logs", alias="DESKTOP_LOG_DIR")

    # Local database (independent from website MySQL; SQLite preferred per SRS)
    local_db_engine: str = Field(default="sqlite", alias="LOCAL_DB_ENGINE")
    local_db_path: Path = Field(
        default=_DATA_ROOT / "data" / "local_election.db",
        alias="LOCAL_DB_PATH",
    )
    local_db_host: str = Field(default="localhost", alias="LOCAL_DB_HOST")
    local_db_port: int = Field(default=3306, alias="LOCAL_DB_PORT")
    local_db_name: str = Field(default="local_election", alias="LOCAL_DB_NAME")
    local_db_user: str = Field(default="root", alias="LOCAL_DB_USER")
    local_db_password: str = Field(default="", alias="LOCAL_DB_PASSWORD")

    sync_uploads_enabled: bool = Field(default=True, alias="SYNC_UPLOADS_ENABLED")
    sync_batch_size: int = Field(default=20, alias="SYNC_BATCH_SIZE")
    sync_poll_interval_ms: int = Field(default=200, alias="SYNC_POLL_INTERVAL_MS")

    heartbeat_enabled: bool = Field(default=True, alias="HEARTBEAT_ENABLED")
    heartbeat_interval_seconds: float = Field(default=10.0, alias="HEARTBEAT_INTERVAL_SECONDS")

    @property
    def local_database_url(self) -> str:
        """SQLAlchemy URL for the desktop local cache database."""
        if self.local_db_engine.lower() == "mysql":
            return (
                f"mysql+pymysql://{self.local_db_user}:{self.local_db_password}"
                f"@{self.local_db_host}:{self.local_db_port}/{self.local_db_name}"
            )
        self.local_db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{self.local_db_path}"


@lru_cache
def get_settings() -> DesktopSettings:
    return DesktopSettings()


settings = get_settings()
