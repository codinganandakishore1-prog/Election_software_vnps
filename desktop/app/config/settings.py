"""Desktop application configuration."""

from functools import lru_cache
from pathlib import Path

from election_platform.config.base import BaseAppSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

DESKTOP_ROOT = Path(__file__).resolve().parents[2]


class DesktopSettings(BaseAppSettings):
    """Desktop-specific settings."""

    model_config = SettingsConfigDict(
        env_file=DESKTOP_ROOT.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    website_url: str = Field(default="http://localhost:8000", alias="WEBSITE_URL")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    node_id: str = Field(default="", alias="NODE_ID")
    node_secret: str = Field(default="", alias="NODE_SECRET")
    config_dir: Path = Field(default=DESKTOP_ROOT / "data" / "config", alias="DESKTOP_CONFIG_DIR")
    log_dir: Path = Field(default=DESKTOP_ROOT / "logs", alias="DESKTOP_LOG_DIR")

    # Local database (independent from website MySQL)
    local_db_host: str = Field(default="localhost", alias="LOCAL_DB_HOST")
    local_db_port: int = Field(default=3306, alias="LOCAL_DB_PORT")
    local_db_name: str = Field(default="local_election", alias="LOCAL_DB_NAME")
    local_db_user: str = Field(default="root", alias="LOCAL_DB_USER")
    local_db_password: str = Field(default="", alias="LOCAL_DB_PASSWORD")


@lru_cache
def get_settings() -> DesktopSettings:
    return DesktopSettings()


settings = get_settings()
