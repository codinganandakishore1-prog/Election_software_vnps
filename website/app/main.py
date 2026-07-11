"""NiceGUI website entry point."""

from election_platform.logging.setup import get_logger, setup_logging
from nicegui import ui

from website.app.config.settings import settings
from website.app.dependencies.container import get_website_container

logger = get_logger("website.application")


def register_routes() -> None:
    """Register placeholder routes. UI pages deferred to later phase."""

    @ui.page("/")
    def index() -> None:
        ui.label(f"{settings.app_name} — Website Scaffold").classes("text-h4 q-pa-md")
        ui.label("Administration portal placeholder. UI implementation deferred.").classes("q-pa-md")


def main() -> None:
    """Start the NiceGUI website."""
    from pathlib import Path
    log_dir = Path(__file__).resolve().parents[1] / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir, app_name="website", log_level=settings.log_level)
    get_website_container(settings.backend_url)
    register_routes()
    ui.run(host=settings.host, port=settings.port, reload=settings.reload, title=settings.app_name)


if __name__ in {"__main__", "__mp_main__"}:
    main()
