"""Theme and branding management page."""

from __future__ import annotations

import base64
from typing import Any

from nicegui import events, ui

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.services.auth_service import AuthService
from app.services.theme_service import ThemeService
from app.theme import apply_saved_theme, inject_theme

ROLE_CAN_EDIT = {"Administrator", "Super Administrator"}

FONT_OPTIONS = [
    "Inter",
    "Roboto",
    "Open Sans",
    "Oswald",
    "Montserrat",
    "Playfair Display",
    "Merriweather",
    "Lato",
    "Poppins",
    "Times New Roman",
]

COLOR_FIELDS = [
    ("primary_color", "Primary"),
    ("secondary_color", "Secondary"),
    ("accent_color", "Accent"),
    ("warning_color", "Warning"),
    ("danger_color", "Danger"),
    ("background_color", "Background"),
    ("surface_color", "Surface"),
    ("text_primary_color", "Text Primary"),
    ("text_secondary_color", "Text Secondary"),
]

LOGO_ASSETS = [
    ("school_logo", "School Logo", "Upload the school emblem shown on voting screens."),
    ("election_logo", "Election Logo", "Upload the election-specific branding logo."),
]

BACKGROUND_ASSETS = [
    ("background_welcome", "Welcome Background", "Shown on the school welcome screen."),
    ("background_light", "Light Background", "Used for light-themed voting screens."),
    ("background_dark", "Dark Background", "Used for dark-themed voting screens."),
]

ICON_ASSETS = [
    ("icon_app", "Application Icon", "Square icon for the desktop voting application."),
    ("icon_favicon", "Favicon", "Small icon for browser tabs and shortcuts."),
]


def _can_edit() -> bool:
    return AuthService.get_user().get("role") in ROLE_CAN_EDIT


def register_theme_routes() -> None:
    """Register the theme and branding management page."""

    @ui.page("/theme-branding")
    @require_auth
    def theme_branding_page() -> None:
        inject_theme()
        apply_saved_theme()

        state: dict[str, Any] = {
            "themes": [],
            "selected_id": "",
            "detail": None,
            "preview_urls": {},
        }

        with admin_shell("/theme-branding") as content:
            with content:
                with ui.row().classes("items-center justify-between q-mb-lg w-full"):
                    with ui.column().classes("gap-0"):
                        ui.label("Theme & Branding").classes("emp-page-title")
                        ui.label(
                            "Manage school logos, backgrounds, fonts, colors, and downloadable theme assets."
                        ).classes("emp-page-subtitle")

                    with ui.row().classes("q-gutter-sm"):
                        if _can_edit():
                            ui.button("New Theme", icon="add", on_click=lambda: open_create_dialog()).props(
                                "outline color=primary"
                            )
                        ui.button("Download Assets", icon="download", on_click=lambda: download_assets()).props(
                            "unelevated color=primary"
                        )
                        if _can_edit():
                            ui.button("Set Active", icon="check_circle", on_click=lambda: activate_theme()).props(
                                "unelevated color=positive"
                            )

                if not AuthService.has_backend_token():
                    ui.label(
                        "No backend API token in session. Connect to the API with valid credentials "
                        "to manage themes."
                    ).classes("text-warning text-caption q-mb-md")

                with ui.row().classes("w-full q-col-gutter-md"):
                    list_container = ui.column().classes("col-12 col-md-3 q-gutter-sm")
                    editor_container = ui.column().classes("col-12 col-md-9 q-gutter-md")

                create_dialog = ui.dialog()
                create_name = ui.input("Theme Name", placeholder="e.g. Council Elections 2026").props(
                    "outlined dense"
                ).classes("w-full")
                create_error = ui.label("").classes("text-negative text-caption")
                create_error.visible = False

                async def load_themes() -> None:
                    success, message, themes = await ThemeService.list_themes()
                    if not success:
                        ui.notify(message or "Could not load themes", type="warning")
                        return
                    state["themes"] = themes
                    if themes and not state["selected_id"]:
                        active = next((theme for theme in themes if theme.get("active")), themes[0])
                        state["selected_id"] = active["id"]
                    render_theme_list()
                    if state["selected_id"]:
                        await load_detail(state["selected_id"])

                async def load_detail(theme_id: str) -> None:
                    success, message, detail = await ThemeService.get_theme(theme_id)
                    if not success:
                        ui.notify(message or "Could not load theme", type="warning")
                        return
                    state["detail"] = detail
                    state["selected_id"] = theme_id
                    state["preview_urls"] = {}
                    await refresh_previews()
                    render_editor()

                async def refresh_previews() -> None:
                    detail = state.get("detail")
                    if not detail:
                        return
                    theme_id = detail["id"]
                    if not ThemeService._auth_headers():
                        return
                    from app.dependencies.container import get_website_container

                    api = get_website_container().api_client
                    for asset_type in ThemeService.ASSET_TYPES:
                        path_key = f"{asset_type}_path"
                        if not detail.get(path_key):
                            state["preview_urls"][asset_type] = None
                            continue
                        response = await api.download(
                            f"/themes/{theme_id}/assets/{asset_type}",
                            headers=ThemeService._auth_headers(),
                        )
                        if response.status_code == 200:
                            encoded = base64.b64encode(response.content).decode()
                            state["preview_urls"][asset_type] = f"data:image/png;base64,{encoded}"

                def render_theme_list() -> None:
                    list_container.clear()
                    with list_container:
                        ui.label("Themes").classes("text-subtitle2 text-weight-medium q-mb-xs")
                        for theme in state["themes"]:
                            is_selected = theme["id"] == state["selected_id"]
                            is_active = theme.get("active", False)

                            def make_select(tid: str):
                                async def select_theme() -> None:
                                    state["selected_id"] = tid
                                    await load_detail(tid)

                                return select_theme

                            with ui.card().classes(
                                f"w-full emp-card cursor-pointer {'ring-2 ring-primary' if is_selected else ''}"
                            ).on("click", make_select(theme["id"])):
                                with ui.row().classes("items-center justify-between w-full"):
                                    with ui.column().classes("gap-0"):
                                        ui.label(theme.get("theme_name", "Untitled")).classes("text-weight-medium")
                                        ui.label(theme.get("school_name") or "No school name").classes(
                                            "text-caption text-grey-7"
                                        )
                                    if is_active:
                                        ui.badge("Active", color="positive").props("outline")

                def render_editor() -> None:
                    editor_container.clear()
                    detail = state.get("detail")
                    if not detail:
                        with editor_container:
                            ui.label("Select or create a theme to begin.").classes("text-grey-7")
                        return

                    with editor_container:
                        with ui.row().classes("items-center justify-between w-full"):
                            with ui.column().classes("gap-0"):
                                ui.label(detail.get("theme_name", "")).classes("text-h6 text-weight-bold")
                                status = "Active theme" if detail.get("active") else "Inactive"
                                ui.label(status).classes(
                                    f"text-caption {'text-positive' if detail.get('active') else 'text-grey-7'}"
                                )
                            if _can_edit() and not detail.get("active"):
                                ui.button(
                                    "Delete",
                                    icon="delete",
                                    on_click=lambda: delete_theme(),
                                ).props("flat color=negative dense")

                        tabs = ui.tabs().classes("w-full")
                        with tabs:
                            ui.tab("General")
                            ui.tab("Logos")
                            ui.tab("Backgrounds")
                            ui.tab("Colors")
                            ui.tab("Fonts")
                            ui.tab("Icons")

                        panels = ui.tab_panels(tabs, value="General").classes("w-full")
                        with panels:
                            with ui.tab_panel("General"):
                                render_general_tab(detail)
                            with ui.tab_panel("Logos"):
                                render_asset_section(LOGO_ASSETS)
                            with ui.tab_panel("Backgrounds"):
                                render_asset_section(BACKGROUND_ASSETS)
                            with ui.tab_panel("Colors"):
                                render_colors_tab(detail)
                            with ui.tab_panel("Fonts"):
                                render_fonts_tab(detail)
                            with ui.tab_panel("Icons"):
                                render_asset_section(ICON_ASSETS)

                def render_general_tab(detail: dict[str, Any]) -> None:
                    name_input = ui.input("Theme Name", value=detail.get("theme_name", "")).props(
                        "outlined dense"
                    ).classes("w-full")
                    school_input = ui.input("School Name", value=detail.get("school_name") or "").props(
                        "outlined dense"
                    ).classes("w-full")

                    if _can_edit():

                        async def save_general() -> None:
                            payload = {
                                "theme_name": name_input.value,
                                "school_name": school_input.value or None,
                            }
                            success, message, updated = await ThemeService.update_theme(detail["id"], payload)
                            if success:
                                ui.notify("Theme updated", type="positive")
                                state["detail"] = updated
                                await load_themes()
                            else:
                                ui.notify(message or "Update failed", type="negative")

                        ui.button("Save General", icon="save", on_click=save_general).props("unelevated color=primary")

                def render_colors_tab(detail: dict[str, Any]) -> None:
                    color_inputs: dict[str, Any] = {}
                    with ui.row().classes("w-full q-col-gutter-md"):
                        for field, label in COLOR_FIELDS:
                            with ui.column().classes("col-12 col-sm-6 col-md-4"):
                                color_inputs[field] = ui.color_input(
                                    label,
                                    value=detail.get(field) or "#000000",
                                ).props("outlined dense").classes("w-full")

                    if _can_edit():

                        async def save_colors() -> None:
                            payload = {field: color_inputs[field].value for field, _ in COLOR_FIELDS}
                            success, message, updated = await ThemeService.update_theme(detail["id"], payload)
                            if success:
                                ui.notify("Colors saved", type="positive")
                                state["detail"] = updated
                            else:
                                ui.notify(message or "Save failed", type="negative")

                        ui.button("Save Colors", icon="palette", on_click=save_colors).props("unelevated color=primary")

                def render_fonts_tab(detail: dict[str, Any]) -> None:
                    heading_font = ui.select(
                        options=FONT_OPTIONS,
                        label="Heading Font",
                        value=detail.get("font_heading") or "Inter",
                    ).props("outlined dense").classes("w-full")
                    body_font = ui.select(
                        options=FONT_OPTIONS,
                        label="Body Font",
                        value=detail.get("font_body") or "Inter",
                    ).props("outlined dense").classes("w-full")
                    accent_font = ui.select(
                        options=FONT_OPTIONS,
                        label="Accent Font",
                        value=detail.get("font_accent") or "Playfair Display",
                    ).props("outlined dense").classes("w-full")

                    if _can_edit():

                        async def save_fonts() -> None:
                            payload = {
                                "font_heading": heading_font.value,
                                "font_body": body_font.value,
                                "font_accent": accent_font.value,
                            }
                            success, message, updated = await ThemeService.update_theme(detail["id"], payload)
                            if success:
                                ui.notify("Fonts saved", type="positive")
                                state["detail"] = updated
                            else:
                                ui.notify(message or "Save failed", type="negative")

                        ui.button("Save Fonts", icon="text_fields", on_click=save_fonts).props("unelevated color=primary")

                def render_asset_section(assets: list[tuple[str, str, str]]) -> None:
                    detail = state.get("detail")
                    if not detail:
                        return

                    with ui.row().classes("w-full q-col-gutter-md"):
                        for asset_type, title, description in assets:
                            with ui.column().classes("col-12 col-md-6"):
                                with ui.card().classes("emp-card w-full"):
                                    ui.label(title).classes("text-subtitle1 text-weight-medium")
                                    ui.label(description).classes("text-caption text-grey-7 q-mb-sm")
                                    preview = state["preview_urls"].get(asset_type)
                                    if preview:
                                        ui.image(preview).classes("w-full rounded-borders").style(
                                            "max-height: 180px; object-fit: contain;"
                                        )
                                    else:
                                        with ui.column().classes("items-center justify-center emp-placeholder q-pa-md"):
                                            ui.icon("image", size="lg").classes("text-grey-5")
                                            ui.label("No image uploaded").classes("text-caption text-grey-6")

                                    if _can_edit():

                                        async def make_upload_handler(at: str, asset_title: str):
                                            async def handle_upload(event: events.UploadEventArguments) -> None:
                                                success, message, _ = await ThemeService.upload_asset(
                                                    detail["id"],
                                                    at,
                                                    event.file.name,
                                                    await event.file.read(),
                                                    event.file.content_type or "image/png",
                                                )
                                                if success:
                                                    ui.notify(f"{asset_title} uploaded", type="positive")
                                                    await load_detail(detail["id"])
                                                else:
                                                    ui.notify(message or "Upload failed", type="negative")

                                            return handle_upload

                                        ui.upload(
                                            label="Upload Image",
                                            auto_upload=True,
                                            on_upload=make_upload_handler(asset_type, title),
                                        ).props("accept=.png,.jpg,.jpeg,.webp flat dense color=primary").classes(
                                            "w-full q-mt-sm"
                                        )

                def open_create_dialog() -> None:
                    create_name.value = ""
                    create_error.visible = False
                    create_error.text = ""
                    create_dialog.open()

                async def create_theme() -> None:
                    name = (create_name.value or "").strip()
                    if not name:
                        create_error.text = "Theme name is required"
                        create_error.visible = True
                        return
                    success, message, theme = await ThemeService.create_theme({"theme_name": name})
                    if not success:
                        create_error.text = message or "Could not create theme"
                        create_error.visible = True
                        return
                    create_dialog.close()
                    ui.notify("Theme created", type="positive")
                    state["selected_id"] = theme["id"]
                    await load_themes()

                async def activate_theme() -> None:
                    detail = state.get("detail")
                    if not detail:
                        return
                    success, message, updated = await ThemeService.activate_theme(detail["id"])
                    if success:
                        ui.notify("Theme activated", type="positive")
                        state["detail"] = updated
                        await load_themes()
                    else:
                        ui.notify(message or "Activation failed", type="negative")

                async def delete_theme() -> None:
                    detail = state.get("detail")
                    if not detail:
                        return
                    success, message = await ThemeService.delete_theme(detail["id"])
                    if success:
                        ui.notify("Theme deleted", type="positive")
                        state["selected_id"] = ""
                        state["detail"] = None
                        await load_themes()
                    else:
                        ui.notify(message or "Delete failed", type="negative")

                async def download_assets() -> None:
                    detail = state.get("detail")
                    if not detail:
                        ui.notify("Select a theme first", type="warning")
                        return
                    success, message, _ = await ThemeService.prepare_download(detail["id"])
                    if not success:
                        ui.notify(message or "Could not prepare package", type="negative")
                        return
                    ok, dl_message, content, filename = await ThemeService.download_package(detail["id"])
                    if ok and content:
                        ui.download(content, filename)
                        ui.notify("Theme package downloaded", type="positive")
                    else:
                        ui.notify(dl_message or "Download failed", type="negative")

                with create_dialog, ui.card().classes("emp-card").style("min-width: 360px") as create_card:
                    ui.label("Create Theme").classes("text-h6 q-mb-md")
                    create_name.move(create_card)
                    create_error.move(create_card)
                    with ui.row().classes("justify-end q-gutter-sm q-mt-md w-full"):
                        ui.button("Cancel", on_click=create_dialog.close).props("flat")
                        ui.button("Create", on_click=create_theme).props("unelevated color=primary")

                ui.timer(0.1, load_themes, once=True)

    @ui.page("/settings")
    @require_auth
    def settings_page() -> None:
        ui.navigate.to("/theme-branding")
