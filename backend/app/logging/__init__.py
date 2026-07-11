"""Backend logging setup."""

from election_platform.logging.setup import get_logger, setup_logging

from app.config.settings import settings


def init_logging() -> None:
    """Initialize backend log handlers."""
    setup_logging(
        log_dir=settings.log_folder,
        app_name="backend",
        log_level=settings.log_level,
    )


__all__ = ["init_logging", "get_logger"]
