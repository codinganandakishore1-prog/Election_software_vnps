"""CustomTkinter desktop application entry point."""

from __future__ import annotations

import customtkinter as ctk
from election_platform.logging.setup import get_logger, setup_logging

from app.config.settings import settings
from app.dependencies.container import DESKTOP_ROOT, get_desktop_container
from app.ui.background_manager import BackgroundManager
from app.ui.screens.admin_login import AdminLoginScreen
from app.ui.screens.admin_panel import AdminPanelScreen
from app.ui.screens.settings_screen import SettingsScreen
from app.ui.screens.voting_screen import VotingScreen

logger = get_logger("desktop.application")


class DesktopApp:
    """Main desktop voting application."""

    def __init__(self) -> None:
        self.container = get_desktop_container(settings.website_url)
        self.mode_state = {"mode": "dark"}
        ctk.set_appearance_mode(self.mode_state["mode"])

        self.root = ctk.CTk()
        self.root.title("Node - Election App")

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

        self.bg_manager = BackgroundManager(
            self.root,
            self.container.store.data,
            get_ballot_frame=self._get_ballot_frame,
            base_dir=str(DESKTOP_ROOT),
        )

        self.next_vote_btn = self._create_vote_button()
        self.voting_screen = VotingScreen(
            root=self.root,
            store=self.container.store,
            vote_service=self.container.vote_service,
            bg_manager=self.bg_manager,
            next_vote_btn=self.next_vote_btn,
        )
        self.next_vote_btn.configure(command=self.voting_screen.start_session)

        self.settings_screen = SettingsScreen(
            root=self.root,
            store=self.container.store,
            bg_manager=self.bg_manager,
            mode_state=self.mode_state,
        )

        self.admin_login = AdminLoginScreen(
            root=self.root,
            store=self.container.store,
            on_success=self._open_admin_panel,
        )

        self._build_utility_tray()
        self.bg_manager.refresh_welcome()
        self.container.sync_manager.start()
        self.container.heartbeat_manager.start()

    def _get_ballot_frame(self):
        return self.voting_screen.get_ballot_frame()

    def _create_vote_button(self) -> ctk.CTkButton:
        button = ctk.CTkButton(
            self.root,
            text="TAP TO VOTE",
            font=("Arial", 24, "bold"),
            width=380,
            height=85,
            corner_radius=20,
            border_width=5,
            border_color="#404040",
            fg_color="#2b2b2b",
            hover_color="#353535",
            text_color="#FFFFFF",
            border_spacing=0,
        )
        button.place(relx=0.49, rely=0.70, anchor="nw")
        return button

    def _build_utility_tray(self) -> None:
        utility_tray = ctk.CTkFrame(self.root, fg_color="transparent")
        utility_tray.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)

        ctk.CTkButton(
            utility_tray,
            text="⚙️",
            width=110,
            fg_color="#2b2b2b",
            hover_color="#3a3a3a",
            command=self.settings_screen.open,
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            utility_tray,
            text="🔒",
            width=110,
            fg_color="#2b2b2b",
            hover_color="#3a3a3a",
            command=self.admin_login.open,
        ).pack(side="left", padx=5)

    def _open_admin_panel(self) -> None:
        AdminPanelScreen(
            root=self.root,
            store=self.container.store,
            config_service=self.container.config_service,
            sync_manager=self.container.sync_manager,
            diagnostics_service=self.container.diagnostics_service,
        ).open()

    def run(self) -> None:
        logger.info("Desktop voting application started")
        self.root.mainloop()
        self.container.heartbeat_manager.stop()
        self.container.sync_manager.stop()


def main() -> None:
    """Start the desktop voting application."""
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    settings.config_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=settings.log_dir, app_name="desktop", log_level=settings.log_level)
    DesktopApp().run()


if __name__ == "__main__":
    main()
