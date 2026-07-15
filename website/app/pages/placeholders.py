"""Placeholder routes for future business modules."""

from nicegui import ui

from app.components.layout import admin_shell
from app.data.mock import PLACEHOLDER_PAGES
from app.dependencies.auth import require_auth
from app.theme import apply_saved_theme, inject_theme


def _placeholder_content(title: str, subtitle: str, icon: str) -> None:
    with ui.column().classes("items-center emp-placeholder q-mt-md"):
        ui.icon(icon, size="xl").classes("text-grey-5 q-mb-md")
        ui.label(title).classes("text-h6 text-weight-medium")
        ui.label(subtitle).classes("text-body2 q-mt-sm")
        ui.label("This module will be implemented in a later phase.").classes("text-caption text-grey-6 q-mt-md")


def register_placeholder_routes() -> None:
    """Register shell-wrapped placeholder pages for each nav item."""

    for route, meta in PLACEHOLDER_PAGES.items():

        def make_page(r: str, m: dict[str, str]):
            @ui.page(r)
            @require_auth
            def page() -> None:
                inject_theme()
                apply_saved_theme()

                with admin_shell(r) as content:
                    with content:
                        ui.label(m["title"]).classes("emp-page-title")
                        ui.label(m["subtitle"]).classes("emp-page-subtitle q-mb-md")
                        _placeholder_content(m["title"], m["subtitle"], m["icon"])

            return page

        make_page(route, meta)
