"""Backend logging setup."""

from election_platform.logging.setup import get_logger, setup_logging

from app.config.settings import settings


def init_logging() -> None:
    """Initialize backend log handlers."""
    # Prefer stdout on production hosts (Render captures process logs).
    log_to_file = settings.log_to_file if not settings.is_production else False
    setup_logging(
        log_dir=settings.log_folder if log_to_file else None,
        app_name="backend",
        log_level=settings.log_level,
        log_to_file=log_to_file,
    )


__all__ = ["init_logging", "get_logger"]
