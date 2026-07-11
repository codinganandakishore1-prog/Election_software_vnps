"""Website configuration."""

from functools import lru_cache
from pathlib import Path

from election_platform.config.base import BaseAppSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

WEBSITE_ROOT = Path(__file__).resolve().parents[2]


class WebsiteSettings(BaseAppSettings):
    """Website-specific settings."""

    model_config = SettingsConfigDict(
        env_file=WEBSITE_ROOT.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    backend_url: str = Field(default="http://localhost:8000", alias="BACKEND_URL")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    host: str = Field(default="0.0.0.0", alias="WEBSITE_HOST")
    port: int = Field(default=8080, alias="WEBSITE_PORT")
    reload: bool = Field(default=False, alias="WEBSITE_RELOAD")


@lru_cache
def get_settings() -> WebsiteSettings:
    return WebsiteSettings()


settings = get_settings()
