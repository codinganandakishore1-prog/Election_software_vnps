"""Website configuration."""

from functools import lru_cache
from pathlib import Path
import os

from election_platform.config.base import BaseAppSettings
from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict

WEBSITE_ROOT = Path(__file__).resolve().parents[2]

_DEFAULT_BACKEND = "http://localhost:8000"
_WEAK_STORAGE_SECRETS = frozenset(
    {
        "dev-website-storage-secret-change-in-production",
        "change-me-in-production-use-a-long-random-string",
    }
)


class WebsiteSettings(BaseAppSettings):
    """Website-specific settings."""

    model_config = SettingsConfigDict(
        env_file=WEBSITE_ROOT.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    backend_url: str = Field(default=_DEFAULT_BACKEND, alias="BACKEND_URL")
    backend_host: str | None = Field(default=None, alias="BACKEND_HOST")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    host: str = Field(default="0.0.0.0", alias="WEBSITE_HOST")
    port: int = Field(default=8080, alias="WEBSITE_PORT")
    reload: bool = Field(default=False, alias="WEBSITE_RELOAD")
    storage_secret: str = Field(
        default="dev-website-storage-secret-change-in-production",
        alias="WEBSITE_STORAGE_SECRET",
    )
    log_to_file: bool = Field(default=True, alias="LOG_TO_FILE")

    @model_validator(mode="after")
    def _apply_platform_overrides(self) -> "WebsiteSettings":
        # Prefer Render/Docker PORT when present.
        platform_port = os.getenv("PORT")
        if platform_port:
            object.__setattr__(self, "port", int(platform_port))

        # Prefer BACKEND_HOST on Render private network when BACKEND_URL is unset
        # or still the local default. An explicit non-default BACKEND_URL wins.
        explicit_url = (self.backend_url or "").strip()
        host = (self.backend_host or "").strip()
        using_default_url = not explicit_url or explicit_url == _DEFAULT_BACKEND
        if host and using_default_url:
            if host.startswith("http://") or host.startswith("https://"):
                resolved = host
            else:
                resolved = f"http://{host}"
            object.__setattr__(self, "backend_url", resolved.rstrip("/"))
        elif explicit_url:
            object.__setattr__(self, "backend_url", explicit_url.rstrip("/"))
        else:
            object.__setattr__(self, "backend_url", _DEFAULT_BACKEND)

        if self.environment == "production":
            if self.storage_secret in _WEAK_STORAGE_SECRETS or len(self.storage_secret) < 32:
                raise ValueError(
                    "WEBSITE_STORAGE_SECRET must be a strong secret (at least 32 characters) in production"
                )
        return self


@lru_cache
def get_settings() -> WebsiteSettings:
    return WebsiteSettings()


settings = get_settings()
