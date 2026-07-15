"""Authentication service with required backend JWT for API access."""

from __future__ import annotations

from nicegui import app

from app.dependencies.container import get_website_container


class AuthService:
    """Session-based authentication using NiceGUI user storage + backend JWT."""

    @staticmethod
    def is_authenticated() -> bool:
        return bool(app.storage.user.get("authenticated") and AuthService.has_backend_token())

    @staticmethod
    def get_user() -> dict:
        return {
            "username": app.storage.user.get("username", ""),
            "display_name": app.storage.user.get("display_name", ""),
            "role": app.storage.user.get("role", ""),
            "user_id": app.storage.user.get("user_id", ""),
            "email": app.storage.user.get("email", ""),
        }

    @staticmethod
    def update_session_profile(
        *,
        username: str | None = None,
        display_name: str | None = None,
        role: str | None = None,
        user_id: str | None = None,
        email: str | None = None,
    ) -> None:
        if username is not None:
            app.storage.user["username"] = username
        if display_name is not None:
            app.storage.user["display_name"] = display_name
        if role is not None:
            app.storage.user["role"] = role
        if user_id is not None:
            app.storage.user["user_id"] = user_id
        if email is not None:
            app.storage.user["email"] = email

    @staticmethod
    def get_access_token() -> str | None:
        token = app.storage.user.get("access_token")
        return token if token else None

    @staticmethod
    def has_backend_token() -> bool:
        return bool(AuthService.get_access_token())

    @staticmethod
    def _apply_login_session(data: dict, *, remember: bool = False) -> None:
        username = (data.get("username") or "").strip()
        display_name = (data.get("full_name") or username or "").strip()
        role = (data.get("role") or "").strip()
        app.storage.user["authenticated"] = True
        app.storage.user["username"] = username
        app.storage.user["display_name"] = display_name
        app.storage.user["role"] = role
        app.storage.user["user_id"] = data.get("user_id") or data.get("id") or ""
        app.storage.user["email"] = data.get("email") or ""
        app.storage.user["remember"] = remember
        app.storage.user["access_token"] = data["access_token"]
        if data.get("refresh_token"):
            app.storage.user["refresh_token"] = data["refresh_token"]

    @staticmethod
    async def login(username: str, password: str, remember: bool = False) -> tuple[bool, str]:
        """Validate credentials against the API and store the JWT session."""
        user_key = username.strip()
        if not user_key or not password:
            return False, "Enter your username and password."

        success, message, data = await AuthService._backend_login(user_key, password)
        if not success or not isinstance(data, dict) or not data.get("access_token"):
            return (
                False,
                message
                or "Invalid username or password.",
            )

        # Keep entered casing normalized to what the API returned where possible.
        if not data.get("username"):
            data["username"] = user_key.strip().lower()

        AuthService._apply_login_session(data, remember=remember)

        # Prefer authoritative profile fields from /users/me.
        profile_ok, _, profile = await AuthService._fetch_me(data["access_token"])
        if profile_ok and isinstance(profile, dict):
            AuthService.update_session_profile(
                username=profile.get("username") or app.storage.user.get("username"),
                display_name=profile.get("full_name")
                or profile.get("username")
                or app.storage.user.get("display_name"),
                role=profile.get("role") or app.storage.user.get("role"),
                user_id=profile.get("id") or app.storage.user.get("user_id"),
                email=profile.get("email") or "",
            )

        return True, "Signed in successfully."

    @staticmethod
    async def _backend_login(username: str, password: str) -> tuple[bool, str, dict | None]:
        """Authenticate against the backend API."""
        try:
            client = get_website_container().api_client
            response = await client.post(
                "/auth/login",
                json={"username": username.strip().lower(), "password": password},
            )
            success, message, data = client.parse_response(response)
            if not success:
                # Prefer clear credential errors over generic envelope text.
                lowered = (message or "").lower()
                if response.status_code in {401, 403} or "invalid" in lowered:
                    return False, "Invalid username or password.", None
                if response.status_code >= 500:
                    return False, "Sign-in service is unavailable. Try again shortly.", None
            return success, message, data
        except Exception as exc:  # noqa: BLE001
            return False, f"Cannot reach the sign-in service: {exc}", None

    @staticmethod
    async def _fetch_me(access_token: str) -> tuple[bool, str, dict | None]:
        try:
            client = get_website_container().api_client
            response = await client.get(
                "/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return client.parse_response(response)
        except Exception as exc:  # noqa: BLE001
            return False, str(exc), None

    @staticmethod
    def logout() -> None:
        dark_mode = app.storage.user.get("dark_mode", False)
        app.storage.user.clear()
        app.storage.user["dark_mode"] = dark_mode

    @staticmethod
    def clear_stale_session() -> bool:
        """Clear sessions that have no API token. Returns True if cleared."""
        if app.storage.user.get("authenticated") and not AuthService.has_backend_token():
            AuthService.logout()
            return True
        return False

    @staticmethod
    def toggle_dark_mode() -> bool:
        current = app.storage.user.get("dark_mode", False)
        app.storage.user["dark_mode"] = not current
        return not current

    @staticmethod
    def is_dark_mode() -> bool:
        return bool(app.storage.user.get("dark_mode", False))
