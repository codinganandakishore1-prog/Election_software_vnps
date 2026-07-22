"""NiceGUI website entry point."""

import os
from pathlib import Path

from election_platform.logging.setup import get_logger, setup_logging
from nicegui import app, ui

from app.config.settings import settings
from app.dependencies.container import init_website_container
from app.pages import register_all_routes
from app.theme import inject_theme

logger = get_logger("website.application")

BRANDING_DIR = Path(__file__).resolve().parent / "static"


def register_routes() -> None:
    """Register all administration portal routes."""
    inject_theme()
    register_all_routes()


def main() -> None:
    """Start the NiceGUI website."""
    log_to_file = settings.log_to_file if settings.environment != "production" else False
    log_dir = Path(__file__).resolve().parents[1] / "logs"
    setup_logging(
        log_dir=log_dir if log_to_file else None,
        app_name="website",
        log_level=settings.log_level,
        log_to_file=log_to_file,
    )
    if BRANDING_DIR.is_dir():
        app.add_static_files("/branding", str(BRANDING_DIR))
    init_website_container(settings.backend_url, settings.api_prefix)
    register_routes()

    port = int(os.getenv("PORT", str(settings.port)))
    logger.info(
        "Starting website on %s:%s backend=%s env=%s",
        settings.host,
        port,
        settings.backend_url,
        settings.environment,
    )
    favicon = BRANDING_DIR / "school_logo.png"
    ui.run(
        host=settings.host,
        port=port,
        reload=settings.reload and settings.environment != "production",
        title=settings.app_name,
        storage_secret=settings.storage_secret,
        favicon=str(favicon) if favicon.is_file() else None,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
