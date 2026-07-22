"""Fullscreen welcome and voting background management."""

from __future__ import annotations

import os
from typing import Callable

import customtkinter as ctk
from PIL import Image


class BackgroundManager:
    """Layer fullscreen backgrounds behind ballot UI."""

    def __init__(
        self,
        root: ctk.CTk,
        app_data: dict,
        get_ballot_frame: Callable[[], ctk.CTkFrame | None],
        base_dir: str,
    ) -> None:
        self.root = root
        self.app_data = app_data
        self.get_ballot_frame = get_ballot_frame
        self.base_dir = base_dir
        self.bg_label: ctk.CTkLabel | None = None
        self._current_mode = "welcome"
        self._tk_image: ctk.CTkImage | None = None
        # Cache of the last processed image: (path, mtime, width, height)
        self._cache_key: tuple[str, float, int, int] | None = None

    def _resolve_path(self, path: str) -> str:
        if not path:
            return ""
        if os.path.isabs(path) and os.path.exists(path):
            return path
        candidate = os.path.join(self.base_dir, path)
        if os.path.exists(candidate):
            return candidate
        if os.path.exists(path):
            return path
        return candidate

    def _appearance_mode(self) -> str:
        return ctk.get_appearance_mode().lower()

    def _background_path(self, screen: str) -> str:
        if screen == "welcome":
            key = "background_path_welcome"
            fallback = "assets/backgrounds/default_welcome_bg.png"
        else:
            mode = self._appearance_mode()
            key = "background_path_dark" if mode == "dark" else "background_path_light"
            fallback = (
                "assets/backgrounds/default_dark_bg.png"
                if mode == "dark"
                else "assets/backgrounds/default_light_bg.png"
            )
        return self._resolve_path(self.app_data.get(key, fallback))

    def _screen_size(self) -> tuple[int, int]:
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        # Before the window is mapped, winfo_width/height report 1 — fall back
        # to the full screen size so the first paint is not a 1x1 image.
        if width < 100 or height < 100:
            width = self.root.winfo_screenwidth()
            height = self.root.winfo_screenheight()
        return width, height

    def _window_scaling(self) -> float:
        """DPI scaling factor CTk applies to widget/image sizes (e.g. 1.5 at 150%)."""
        try:
            return float(ctk.ScalingTracker.get_window_scaling(self.root))
        except Exception:
            return 1.0

    @staticmethod
    def _cover_resize(image: Image.Image, width: int, height: int) -> Image.Image:
        """Scale to fill width x height, cropping overflow (no distortion)."""
        src_w, src_h = image.size
        if src_w <= 0 or src_h <= 0:
            return image.resize((width, height), Image.Resampling.LANCZOS)
        scale = max(width / src_w, height / src_h)
        new_w = max(width, int(src_w * scale + 0.5))
        new_h = max(height, int(src_h * scale + 0.5))
        image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = (new_w - width) // 2
        top = (new_h - height) // 2
        return image.crop((left, top, left + width, top + height))

    def _show_background(self, image_path: str) -> None:
        width, height = self._screen_size()
        if not image_path or not os.path.exists(image_path):
            if self.bg_label is not None:
                self.bg_label.destroy()
                self.bg_label = None
            return

        cache_key = (image_path, os.path.getmtime(image_path), width, height)
        if cache_key != self._cache_key or self._tk_image is None:
            with Image.open(image_path) as source:
                source.load()
                pil_image = self._cover_resize(source.convert("RGB"), width, height)

            # CTk multiplies the requested size by the Windows DPI scaling factor.
            # Compensate so the rendered image matches the window exactly instead
            # of overflowing (which showed only the middle of the image).
            scaling = self._window_scaling()
            logical_size = (
                max(1, round(width / scaling)),
                max(1, round(height / scaling)),
            )
            self._tk_image = ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=logical_size,
            )
            self._cache_key = cache_key

        if self.bg_label is None:
            self.bg_label = ctk.CTkLabel(self.root, text="", image=self._tk_image)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            self.bg_label.configure(image=self._tk_image)
            self.bg_label.image = self._tk_image  # type: ignore[attr-defined]

        self._raise_layers()

    def _raise_layers(self) -> None:
        ballot = self.get_ballot_frame()
        if self.bg_label is not None:
            self.bg_label.lower()
        if ballot is not None and ballot.winfo_exists():
            ballot.lift()

    def refresh_welcome(self) -> None:
        self._current_mode = "welcome"
        self._show_background(self._background_path("welcome"))

    def refresh_voting(self) -> None:
        self._current_mode = "voting"
        self._show_background(self._background_path("voting"))

    def refresh_auto(self) -> None:
        if self._current_mode == "voting":
            self.refresh_voting()
        else:
            self.refresh_welcome()
