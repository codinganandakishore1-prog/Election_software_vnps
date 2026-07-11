"""Base settings shared across applications."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class BaseAppSettings(BaseSettings):
    """Common environment-driven settings."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Election Management Platform"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
