"""Website settings page."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.services.auth_service import AuthService
from app.services.settings_service import SettingsService
from app.theme import apply_saved_theme, inject_theme

ROLE_CAN_EDIT = {"Administrator", "Super Administrator"}


def _can_edit() -> bool:
    return AuthService.get_user().get("role") in ROLE_CAN_EDIT


def register_settings_routes() -> None:
    """Register the website settings page."""

    @ui.page("/settings")
    @require_auth
    def settings_page() -> None:
        inject_theme()
        apply_saved_theme()

        state: dict[str, Any] = {"settings": {}, "database": {}}

        with admin_shell("/settings") as content:
            with content:
                with ui.row().classes("items-center justify-between q-mb-lg w-full"):
                    with ui.column().classes("gap-0"):
                        ui.label("Settings").classes("emp-page-title")
                        ui.label("Configure website, database, and maintenance options.").classes("emp-page-subtitle")

                if not AuthService.has_backend_token():
                    ui.label(
                        "No backend API token in session. Connect to the API with valid credentials "
                        "to manage settings."
                    ).classes("text-warning text-caption q-mb-md")

                with ui.tabs().classes("w-full") as tabs:
                    ui.tab("Website")
                    ui.tab("Database")

                with ui.tab_panels(tabs, value="Website").classes("w-full q-mt-md"):
                    with ui.tab_panel("Website"):
                        school_name = ui.input("School Name").props("outlined dense").classes("w-full")
                        timezone = ui.input("Timezone", value="UTC").props("outlined dense").classes("w-full")
                        primary_color = ui.input("Primary Color", placeholder="#1976D2").props("outlined dense").classes(
                            "w-full"
                        )
                        secondary_color = ui.input("Secondary Color", placeholder="#26A69A").props(
                            "outlined dense"
                        ).classes("w-full")
                        maintenance_mode = ui.switch("Maintenance Mode")
                        website_error = ui.label("").classes("text-negative text-caption")
                        website_error.visible = False

                        if _can_edit():
                            ui.button(
                                "Save Website Settings",
                                icon="save",
                                on_click=lambda: ui.timer(0, save_website_settings, once=True),
                            ).props("unelevated color=primary q-mt-md")

                    with ui.tab_panel("Database"):
                        db_host = ui.input("Host").props("outlined dense").classes("w-full")
                        db_port = ui.number("Port", value=3306, min=1, max=65535, step=1).props("outlined dense").classes(
                            "w-full"
                        )
                        db_name = ui.input("Database Name").props("outlined dense").classes("w-full")
                        db_user = ui.input("Username").props("outlined dense").classes("w-full")
                        db_password = ui.input("Password", password=True, password_toggle_button=True).props(
                            "outlined dense"
                        ).classes("w-full")
                        database_error = ui.label("").classes("text-negative text-caption")
                        database_error.visible = False
                        database_status = ui.label("").classes("text-caption q-mt-sm")

                        with ui.row().classes("q-gutter-sm q-mt-md"):
                            if _can_edit():
                                ui.button(
                                    "Test Connection",
                                    icon="cable",
                                    on_click=lambda: ui.timer(0, test_database_connection, once=True),
                                ).props("outline")
                                ui.button(
                                    "Save Database Settings",
                                    icon="save",
                                    on_click=lambda: ui.timer(0, save_database_settings, once=True),
                                ).props("unelevated color=primary")

                async def load_settings() -> None:
                    success, message, settings_data = await SettingsService.get_settings()
                    if success and settings_data:
                        state["settings"] = settings_data
                        school_name.value = settings_data.get("school_name") or ""
                        timezone.value = settings_data.get("timezone") or "UTC"
                        primary_color.value = settings_data.get("primary_color") or ""
                        secondary_color.value = settings_data.get("secondary_color") or ""
                        maintenance_mode.value = bool(settings_data.get("maintenance_mode"))
                    elif message:
                        ui.notify(message, type="negative")

                    db_success, db_message, database_data = await SettingsService.get_database_settings()
                    if db_success and database_data:
                        state["database"] = database_data
                        db_host.value = database_data.get("host") or ""
                        db_port.value = database_data.get("port") or 3306
                        db_name.value = database_data.get("database_name") or ""
                        db_user.value = database_data.get("username") or ""
                        if database_data.get("password_configured"):
                            database_status.set_text("Password is configured (hidden).")
                    elif db_message:
                        ui.notify(db_message, type="negative")

                async def save_website_settings() -> None:
                    website_error.visible = False
                    payload = {
                        "school_name": (school_name.value or "").strip() or None,
                        "timezone": (timezone.value or "").strip() or None,
                        "primary_color": (primary_color.value or "").strip() or None,
                        "secondary_color": (secondary_color.value or "").strip() or None,
                        "maintenance_mode": bool(maintenance_mode.value),
                    }
                    success, message, _ = await SettingsService.update_settings(payload)
                    if success:
                        ui.notify("Website settings saved", type="positive")
                        await load_settings()
                    else:
                        website_error.text = message or "Could not save settings"
                        website_error.visible = True

                async def save_database_settings() -> None:
                    database_error.visible = False
                    password = db_password.value or ""
                    if not all([db_host.value, db_name.value, db_user.value, password]):
                        database_error.text = "Host, database, username, and password are required."
                        database_error.visible = True
                        return
                    payload = {
                        "host": db_host.value.strip(),
                        "port": int(db_port.value or 3306),
                        "database_name": db_name.value.strip(),
                        "username": db_user.value.strip(),
                        "password": password,
                    }
                    success, message, _ = await SettingsService.update_database_settings(payload)
                    if success:
                        db_password.value = ""
                        ui.notify("Database settings saved", type="positive")
                        await load_settings()
                    else:
                        database_error.text = message or "Could not save database settings"
                        database_error.visible = True

                async def test_database_connection() -> None:
                    database_error.visible = False
                    password = db_password.value or ""
                    if password:
                        payload = {
                            "host": (db_host.value or "").strip(),
                            "port": int(db_port.value or 3306),
                            "database_name": (db_name.value or "").strip(),
                            "username": (db_user.value or "").strip(),
                            "password": password,
                        }
                        success, message, result = await SettingsService.test_database_connection(payload)
                    else:
                        success, message, result = await SettingsService.test_saved_database_connection()

                    if success and result and result.get("success"):
                        ui.notify(result.get("message", "Connection successful"), type="positive")
                    else:
                        detail = (result or {}).get("message") if result else message
                        database_error.text = detail or "Connection failed"
                        database_error.visible = True

                ui.timer(0.1, load_settings, once=True)
