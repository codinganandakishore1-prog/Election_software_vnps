"""Environment-based backend configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from election_platform.config.base import BaseAppSettings
from pydantic import Field, field_validator, model_validator
from pydantic_settings import NoDecode, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseAppSettings):
    """Backend settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # Database (individual fields or DATABASE_URL)
    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")
    database_host: str = Field(default="localhost", alias="DATABASE_HOST")
    database_port: int = Field(default=3306, alias="DATABASE_PORT")
    database_name: str = Field(default="election_db", alias="DATABASE_NAME")
    database_user: str = Field(default="root", alias="DATABASE_USER")
    database_password: str = Field(default="", alias="DATABASE_PASSWORD")
    # When true (or when DATABASE_URL is sqlite), create tables and seed on startup.
    bootstrap_database: bool = Field(default=False, alias="BOOTSTRAP_DATABASE")

    # JWT
    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_expiry_minutes: int = Field(default=720, alias="JWT_EXPIRY")
    jwt_refresh_expiry_days: int = Field(default=30, alias="JWT_REFRESH_EXPIRY_DAYS")
    node_jwt_expiry_hours: int = Field(default=72, alias="NODE_JWT_EXPIRY_HOURS")

    # Paths — defaults resolve under backend/; production/Docker use absolute /data/* paths.
    upload_folder: Path = Field(default=BACKEND_ROOT / "uploads", alias="UPLOAD_FOLDER")
    report_folder: Path = Field(default=BACKEND_ROOT / "generated_reports", alias="REPORT_FOLDER")
    backup_folder: Path = Field(default=BACKEND_ROOT / "backups", alias="BACKUP_FOLDER")
    config_package_folder: Path = Field(
        default=BACKEND_ROOT / "config_packages",
        alias="CONFIG_PACKAGE_FOLDER",
    )
    log_folder: Path = Field(default=BACKEND_ROOT / "logs", alias="LOG_FOLDER")

    # WebSocket
    websocket_timeout: int = Field(default=30, alias="WEBSOCKET_TIMEOUT")

    # Analytics
    analytics_eligible_voters: int | None = Field(default=None, alias="ANALYTICS_ELIGIBLE_VOTERS")

    # API
    api_prefix: str = "/api/v1"
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["*"],
        alias="CORS_ORIGINS",
    )

    # Logging
    log_to_file: bool = Field(default=True, alias="LOG_TO_FILE")

    # Security
    rate_limit_requests: int = Field(default=120, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")
    login_rate_limit_requests: int = Field(default=10, alias="LOGIN_RATE_LIMIT_REQUESTS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: Any) -> list[str]:
        if value is None or value == "":
            return ["*"]
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
            return items or ["*"]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return ["*"]

    @field_validator(
        "upload_folder",
        "report_folder",
        "backup_folder",
        "config_package_folder",
        "log_folder",
        mode="before",
    )
    @classmethod
    def _coerce_path(cls, value: Any) -> Path:
        if value is None or value == "":
            raise ValueError("Path setting cannot be empty")
        return Path(value)

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        if self.environment == "production":
            weak_secrets = {
                "change-me-in-production",
                "change-me-in-production-use-a-long-random-string",
            }
            if self.jwt_secret in weak_secrets or len(self.jwt_secret) < 32:
                raise ValueError(
                    "JWT_SECRET must be a strong secret (at least 32 characters) in production"
                )
            if self.cors_origins == ["*"]:
                raise ValueError(
                    "CORS_ORIGINS must list explicit origins in production (not '*')"
                )
        return self

    @property
    def database_url(self) -> str:
        """SQLAlchemy connection URL (MySQL by default, SQLite when DATABASE_URL is set)."""
        if self.database_url_override:
            url = self.database_url_override.strip()
            if url.startswith("mysql://"):
                return url.replace("mysql://", "mysql+pymysql://", 1)
            if url.startswith("sqlite://") and not url.startswith("sqlite+"):
                return url.replace("sqlite://", "sqlite+pysqlite://", 1)
            return url
        return (
            f"mysql+pymysql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
