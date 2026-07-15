"""Top navigation bar component."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from nicegui import ui

from app.data.mock import ELECTION_NAME, SCHOOL_LOGO_URL, SCHOOL_NAME
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService
from app.websocket.bus import event_bus


def create_header(drawer: ui.left_drawer) -> None:
    """Render the top bar with search, notifications, theme toggle, and user menu."""
    user = AuthService.get_user()
    notifications: list[dict[str, Any]] = []
    notification_container: ui.column | None = None

    def _format_time(value: str | None) -> str:
        if not value:
            return ""
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.strftime("%H:%M")
        except ValueError:
            return value

    def _notification_icon(note_type: str) -> str:
        mapping = {
            "Node Offline": "devices",
            "Node Online": "devices",
            "Election Started": "campaign",
            "Election Published": "publish",
            "Election Ended": "stop_circle",
            "Synchronization Failed": "sync_problem",
            "Synchronization Completed": "sync",
            "Report Downloaded": "download",
            "Administrator Action": "admin_panel_settings",
        }
        return mapping.get(note_type, "notifications")

    def render_notifications() -> None:
        if notification_container is None:
            return
        notification_container.clear()
        with notification_container:
            if not notifications:
                ui.label("No notifications yet.").classes("text-caption text-grey-6 q-pa-sm")
                return
            for note in notifications[:8]:
                with ui.row().classes("items-start q-pa-sm q-gutter-sm"):
                    ui.icon(_notification_icon(note.get("notification_type", "")), size="sm").classes(
                        "text-primary q-mt-xs"
                    )
                    with ui.column().classes("gap-0"):
                        ui.label(note.get("title", "")).classes("text-body2")
                        ui.label(_format_time(note.get("created_at"))).classes("text-caption text-grey-6")

    def on_notification_event(payload: dict[str, Any]) -> None:
        data = payload.get("data")
        if not isinstance(data, dict):
            return
        notifications.insert(0, data)
        del notifications[8:]
        render_notifications()
        ui.notify(data.get("title", "New notification"), type="info")

    event_bus.subscribe("notification", on_notification_event)

    with ui.header().classes("emp-header items-center q-px-md"):
        ui.button(icon="menu", on_click=drawer.toggle).props("flat round dense").classes("lg:hidden")

        with ui.row().classes("items-center q-gutter-sm"):
            ui.image(SCHOOL_LOGO_URL).classes("emp-school-logo emp-school-logo-header")
            with ui.column().classes("gap-0"):
                ui.label(SCHOOL_NAME).classes("text-weight-bold text-body2 leading-tight")
                ui.label(ELECTION_NAME).classes("text-caption text-grey-7 leading-tight hidden sm:block")

        ui.space()

        search = ui.input(placeholder="Search candidates, nodes, reports…").props(
            "dense outlined clearable"
        ).classes("max-w-xs hidden md:block").style("min-width: 220px")

        def on_search(e: object) -> None:
            value = getattr(e, "value", None) or search.value
            if value:
                ui.notify(f'Search for "{value}" — module not yet implemented.', type="info")

        search.on("keydown.enter", on_search)

        with ui.button(icon="notifications").props("flat round dense"):
            with ui.menu().classes("emp-card q-pa-sm").style("min-width: 280px"):
                ui.label("Notifications").classes("text-weight-bold q-pa-sm")
                ui.separator()
                notification_container = ui.column().classes("w-full")

        async def load_notifications() -> None:
            if not AuthService.has_backend_token():
                render_notifications()
                return
            rows = await NotificationService.list_recent()
            notifications.clear()
            notifications.extend(rows)
            render_notifications()

        ui.timer(0.1, load_notifications, once=True)

        def toggle_theme() -> None:
            dark = AuthService.toggle_dark_mode()
            if dark:
                ui.dark_mode().enable()
            else:
                ui.dark_mode().disable()

        ui.button(
            icon="dark_mode" if not AuthService.is_dark_mode() else "light_mode",
            on_click=toggle_theme,
        ).props("flat round dense").tooltip("Toggle dark mode")

        with ui.button().props("flat round dense"):
            ui.icon("account_circle")
            with ui.menu():
                ui.menu_item(
                    f"{user.get('display_name') or user.get('username') or 'User'} · {user.get('role') or 'No role'}"
                ).props("disable")
                ui.separator()
                ui.menu_item("Profile", on_click=lambda: ui.navigate.to("/profile"))
                ui.menu_item("Logout", on_click=_logout_from_menu)


def _logout_from_menu() -> None:
    AuthService.logout()
    ui.navigate.to("/login")
