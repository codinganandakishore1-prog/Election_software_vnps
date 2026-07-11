"""CustomTkinter desktop application entry point."""

import customtkinter as ctk
from election_platform.logging.setup import get_logger, setup_logging

from desktop.app.config.settings import settings
from desktop.app.dependencies.container import get_desktop_container

logger = get_logger("desktop.application")


class DesktopApp:
    """Main desktop application shell (placeholder)."""

    def __init__(self) -> None:
        self.container = get_desktop_container(settings.website_url)
        self.root = ctk.CTk()
        self.root.title(f"{settings.app_name} — Desktop Scaffold")
        self._build_placeholder_ui()

    def _build_placeholder_ui(self) -> None:
        label = ctk.CTkLabel(
            self.root,
            text="Election Voting Application — Architecture Scaffold\nUI implementation deferred.",
            font=ctk.CTkFont(size=16),
        )
        label.pack(padx=40, pady=40)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    """Start the desktop voting application."""
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    settings.config_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=settings.log_dir, app_name="desktop", log_level=settings.log_level)
    logger.info("Starting desktop application scaffold")
    app = DesktopApp()
    app.run()


if __name__ == "__main__":
    main()
