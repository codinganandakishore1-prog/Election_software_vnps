"""Sign-in page for the administration portal."""

from nicegui import ui

from app.config.settings import settings
from app.data.mock import APP_VERSION, ELECTION_NAME, SCHOOL_LOGO_URL, SCHOOL_NAME
from app.services.auth_service import AuthService
from app.theme import apply_saved_theme, inject_theme


def register_login_routes() -> None:
    """Register the public login route."""

    @ui.page("/login")
    def login_page() -> None:
        inject_theme()
        apply_saved_theme()
        AuthService.clear_stale_session()

        if AuthService.is_authenticated():
            ui.navigate.to("/dashboard")
            return

        with ui.column().classes("emp-login-page w-full"):
            with ui.card().classes("emp-login-card"):
                with ui.column().classes("items-center q-mb-lg w-full"):
                    ui.image(SCHOOL_LOGO_URL).classes("emp-school-logo emp-school-logo-login q-mb-sm")
                    ui.label(SCHOOL_NAME).classes("text-h6 text-weight-bold text-center")
                    ui.label("Election Management Platform").classes("text-caption text-grey-7")
                    ui.label(ELECTION_NAME).classes("text-body2 text-primary q-mt-xs")

                ui.label("Sign in").classes("text-h6 text-weight-medium q-mb-xs")
                ui.label("Use your administrator account to continue.").classes(
                    "text-caption text-grey-7 q-mb-md"
                )

                username = (
                    ui.input("Username", placeholder="Enter username")
                    .props("outlined dense autocomplete=username")
                    .classes("w-full")
                )
                password = (
                    ui.input(
                        "Password",
                        placeholder="Enter password",
                        password=True,
                        password_toggle_button=True,
                    )
                    .props("outlined dense autocomplete=current-password")
                    .classes("w-full")
                )
                remember = ui.checkbox("Keep me signed in on this device")

                error_label = ui.label("").classes("text-negative text-caption q-mt-sm")
                error_label.visible = False

                sign_in_button = ui.button("Sign in", icon="login").props(
                    "unelevated color=primary"
                ).classes("w-full q-mt-md")

                async def do_login() -> None:
                    error_label.visible = False
                    sign_in_button.props("loading")
                    try:
                        success, message = await AuthService.login(
                            username.value or "",
                            password.value or "",
                            remember=bool(remember.value),
                        )
                        if success:
                            ui.notify(
                                f"Welcome, {AuthService.get_user().get('display_name') or 'user'}",
                                type="positive",
                            )
                            ui.navigate.to("/dashboard")
                        else:
                            error_label.text = message
                            error_label.visible = True
                    finally:
                        sign_in_button.props(remove="loading")

                sign_in_button.on_click(do_login)
                password.on("keydown.enter", do_login)
                username.on("keydown.enter", do_login)

                if settings.environment != "production":
                    ui.label(
                        "Local accounts: admin / admin123 · viewer / viewer123 · superadmin / super123"
                    ).classes("text-caption text-grey-6 q-mt-md text-center w-full")

                ui.label(f"Version {APP_VERSION}").classes(
                    "text-caption text-grey-6 text-center q-mt-lg w-full"
                )
