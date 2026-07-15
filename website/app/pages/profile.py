"""Signed-in user profile page."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.theme import apply_saved_theme, inject_theme


def register_profile_routes() -> None:
    """Register the profile page."""

    @ui.page("/profile")
    @require_auth
    def profile_page() -> None:
        inject_theme()
        apply_saved_theme()

        state: dict[str, Any] = {"profile": {}}

        with admin_shell("/profile") as content:
            with content:
                with ui.column().classes("gap-0 q-mb-lg"):
                    ui.label("Profile").classes("emp-page-title")
                    ui.label("View your account details and update password.").classes("emp-page-subtitle")

                if not AuthService.has_backend_token():
                    ui.label(
                        "No backend API token in session. Sign in again to manage your profile."
                    ).classes("text-warning text-caption q-mb-md")

                with ui.row().classes("w-full q-col-gutter-md items-stretch"):
                    with ui.column().classes("col-12 col-md-6"):
                        with ui.card().classes("emp-card w-full q-pa-md"):
                            ui.label("Account").classes("text-subtitle1 text-weight-bold q-mb-md")

                            with ui.row().classes("w-full items-center justify-between q-mb-sm"):
                                ui.label("Username").classes("text-caption text-grey-7")
                                username_label = ui.label("—").classes("text-body1 text-weight-medium")
                            with ui.row().classes("w-full items-center justify-between q-mb-md"):
                                ui.label("Role").classes("text-caption text-grey-7")
                                role_label = ui.label("—").classes("text-body1 text-weight-medium")

                            full_name = (
                                ui.input("Full Name").props("outlined dense").classes("w-full")
                            )
                            email = (
                                ui.input("Email").props("outlined dense type=email").classes("w-full")
                            )
                            profile_error = ui.label("").classes("text-negative text-caption")
                            profile_error.visible = False

                            async def save_profile() -> None:
                                profile_error.visible = False
                                payload = {
                                    "full_name": (full_name.value or "").strip() or None,
                                    "email": (email.value or "").strip() or None,
                                }
                                success, message, data = await UserService.update_me(payload)
                                if success and data:
                                    state["profile"] = data
                                    AuthService.update_session_profile(
                                        username=data.get("username"),
                                        display_name=data.get("full_name") or data.get("username"),
                                        role=data.get("role"),
                                        email=data.get("email") or "",
                                    )
                                    ui.notify("Profile saved", type="positive")
                                else:
                                    profile_error.text = message or "Could not save profile"
                                    profile_error.visible = True

                            ui.button(
                                "Save Profile",
                                icon="save",
                                on_click=save_profile,
                            ).props("unelevated color=primary q-mt-md")
                            ui.label(
                                "Username and role are assigned by an administrator and cannot be changed here."
                            ).classes("text-caption text-grey-6 q-mt-sm")

                    with ui.column().classes("col-12 col-md-6"):
                        with ui.card().classes("emp-card w-full q-pa-md"):
                            ui.label("Change Password").classes(
                                "text-subtitle1 text-weight-bold q-mb-md"
                            )
                            ui.label(
                                "New password must be at least 8 characters and include uppercase, "
                                "lowercase, a number, and a special character."
                            ).classes("text-caption text-grey-7 q-mb-sm")
                            current_password = (
                                ui.input(
                                    "Current Password",
                                    password=True,
                                    password_toggle_button=True,
                                )
                                .props("outlined dense")
                                .classes("w-full")
                            )
                            new_password = (
                                ui.input(
                                    "New Password",
                                    password=True,
                                    password_toggle_button=True,
                                )
                                .props("outlined dense")
                                .classes("w-full")
                            )
                            confirm_password = (
                                ui.input(
                                    "Confirm New Password",
                                    password=True,
                                    password_toggle_button=True,
                                )
                                .props("outlined dense")
                                .classes("w-full")
                            )
                            password_error = ui.label("").classes("text-negative text-caption")
                            password_error.visible = False

                            async def save_password() -> None:
                                password_error.visible = False
                                old = current_password.value or ""
                                new = new_password.value or ""
                                confirm = confirm_password.value or ""
                                if not old or not new:
                                    password_error.text = "Current and new password are required."
                                    password_error.visible = True
                                    return
                                if new != confirm:
                                    password_error.text = "New password and confirmation do not match."
                                    password_error.visible = True
                                    return
                                success, message, _ = await UserService.change_password(old, new)
                                if success:
                                    current_password.value = ""
                                    new_password.value = ""
                                    confirm_password.value = ""
                                    ui.notify("Password changed", type="positive")
                                else:
                                    password_error.text = message or "Could not change password"
                                    password_error.visible = True

                            ui.button(
                                "Update Password",
                                icon="lock",
                                on_click=save_password,
                            ).props("unelevated color=primary q-mt-md")

                async def load_profile() -> None:
                    success, message, data = await UserService.get_me()
                    if success and data:
                        state["profile"] = data
                        username_label.set_text(data.get("username") or "—")
                        role_label.set_text(data.get("role") or "—")
                        full_name.value = data.get("full_name") or ""
                        email.value = data.get("email") or ""
                        AuthService.update_session_profile(
                            username=data.get("username"),
                            display_name=data.get("full_name") or data.get("username"),
                            role=data.get("role"),
                            user_id=data.get("id"),
                            email=data.get("email") or "",
                        )
                    elif message:
                        session = AuthService.get_user()
                        username_label.set_text(session.get("username") or "—")
                        role_label.set_text(session.get("role") or "—")
                        ui.notify(message, type="negative")

                ui.timer(0.1, load_profile, once=True)
