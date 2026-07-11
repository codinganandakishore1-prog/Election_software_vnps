"""Environment-based backend configuration."""

from functools import lru_cache
from pathlib import Path

from election_platform.config.base import BaseAppSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseAppSettings):
    """Backend settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_host: str = Field(default="localhost", alias="DATABASE_HOST")
    database_port: int = Field(default=3306, alias="DATABASE_PORT")
    database_name: str = Field(default="election_db", alias="DATABASE_NAME")
    database_user: str = Field(default="root", alias="DATABASE_USER")
    database_password: str = Field(default="", alias="DATABASE_PASSWORD")

    # JWT
    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_expiry_minutes: int = Field(default=60, alias="JWT_EXPIRY")
    jwt_refresh_expiry_days: int = Field(default=7, alias="JWT_REFRESH_EXPIRY_DAYS")
    node_jwt_expiry_hours: int = Field(default=24, alias="NODE_JWT_EXPIRY_HOURS")

    # Paths
    upload_folder: Path = Field(default=BACKEND_ROOT / "uploads", alias="UPLOAD_FOLDER")
    report_folder: Path = Field(default=BACKEND_ROOT / "generated_reports", alias="REPORT_FOLDER")
    backup_folder: Path = Field(default=BACKEND_ROOT / "backups", alias="BACKUP_FOLDER")
    log_folder: Path = Field(default=BACKEND_ROOT / "logs", alias="LOG_FOLDER")

    # WebSocket
    websocket_timeout: int = Field(default=30, alias="WEBSOCKET_TIMEOUT")

    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    @property
    def database_url(self) -> str:
        """SQLAlchemy MySQL connection URL."""
        return (
            f"mysql+pymysql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
