"""Administration shell layout wrapping authenticated pages."""

from contextlib import contextmanager
from typing import Generator

from nicegui import ui

from app.components.header import create_header
from app.components.sidebar import create_sidebar


@contextmanager
def admin_shell(current_route: str) -> Generator[ui.column, None, None]:
    """
    Provide the shared admin layout: responsive sidebar, header, and content area.

    NiceGUI requires top-level layout elements (left_drawer, header) to be direct
    children of the page content — they must not be nested inside a Column/Row.

    Usage:
        with admin_shell("/dashboard") as content:
            with content:
                ui.label("Page content")
    """
    drawer = ui.left_drawer(value=False).props(
        "show-if-above bordered width=260 breakpoint=1024"
    ).classes("emp-sidebar")

    create_sidebar(current_route, drawer)
    create_header(drawer)

    with ui.column().classes("emp-main emp-shell w-full min-h-screen col-grow") as content:
        yield content
