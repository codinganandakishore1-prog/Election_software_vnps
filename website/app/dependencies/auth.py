"""Route authentication guard."""

from collections.abc import Callable
from functools import wraps
from typing import Any

from nicegui import ui

from app.services.auth_service import AuthService


def require_auth(page_fn: Callable[..., Any]) -> Callable[..., Any]:
    """Redirect visitors without a valid API session to the login page."""

    @wraps(page_fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        AuthService.clear_stale_session()
        if not AuthService.is_authenticated():
            ui.navigate.to("/login")
            return None

        async def _refresh_in_background() -> None:
            ok = await AuthService.ensure_fresh_session()
            if not ok:
                AuthService.logout()
                ui.notify("Session expired. Please sign in again.", type="warning")
                ui.navigate.to("/login")

        ui.timer(0.05, _refresh_in_background, once=True)
        return page_fn(*args, **kwargs)

    return wrapper
