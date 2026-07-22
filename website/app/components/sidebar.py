"""Sidebar navigation component."""

from nicegui import ui

from app.data.mock import NAV_ITEMS, SCHOOL_LOGO_URL, SCHOOL_NAME
from app.services.auth_service import AuthService


def create_sidebar(current_route: str, drawer: ui.left_drawer) -> None:
    """Render the persistent sidebar with navigation links."""
    user = AuthService.get_user()

    with drawer:
        with ui.column().classes("emp-sidebar-inner w-full"):
            with ui.row().classes("items-center q-pa-md q-pb-md").style("flex: 0 0 auto"):
                ui.image(SCHOOL_LOGO_URL).classes("emp-school-logo emp-school-logo-sidebar q-mr-sm")
                with ui.column().classes("gap-0"):
                    ui.label("Election Portal").classes("text-weight-bold text-white")
                    ui.label(SCHOOL_NAME).classes("text-caption text-orange-2")
                    ui.label(user.get("role", "")).classes("text-caption text-blue-2")

            ui.separator().classes("bg-white opacity-20 q-mx-md").style("flex: 0 0 auto")

            with ui.element("nav").classes("emp-sidebar-nav"):
                for item in NAV_ITEMS:
                    is_active = current_route == item.route or (
                        current_route == "/" and item.route == "/dashboard"
                    )
                    active_cls = "is-active" if is_active else ""
                    with ui.link(target=item.route).classes(f"emp-sidebar-link {active_cls}"):
                        ui.icon(item.icon)
                        ui.label(item.label).classes("emp-sidebar-link-label text-body2")

            with ui.column().classes("emp-sidebar-footer w-full gap-0"):
                with ui.row().classes("items-center q-mb-sm opacity-90 no-wrap"):
                    ui.icon("account_circle", size="sm").classes("q-mr-sm")
                    with ui.column().classes("gap-0"):
                        ui.label(user.get("display_name") or user.get("username") or "User").classes(
                            "text-caption text-weight-medium"
                        )
                        ui.label(f"{user.get('username', '')} · {user.get('role', '')}").classes(
                            "text-caption opacity-70"
                        )

                ui.button(
                    "Logout",
                    icon="logout",
                    on_click=_logout,
                ).props("flat dense color=white").classes("w-full justify-start")


def _logout() -> None:
    from app.services.auth_service import AuthService

    AuthService.logout()
    ui.navigate.to("/login")
