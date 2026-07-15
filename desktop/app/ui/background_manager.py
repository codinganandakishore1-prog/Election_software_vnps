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
        mode = self._appearance_mode()
        if screen == "welcome":
            key = "background_path_light" if mode == "light" else "background_path_dark"
        else:
            key = "background_path_dark" if mode == "dark" else "background_path_light"
        default = "default_light_bg.png" if mode == "light" else "default_dark_bg.png"
        return self._resolve_path(self.app_data.get(key, default))

    def _screen_size(self) -> tuple[int, int]:
        self.root.update_idletasks()
        width = self.root.winfo_width() or self.root.winfo_screenwidth()
        height = self.root.winfo_height() or self.root.winfo_screenheight()
        return width, height

    def _show_background(self, image_path: str) -> None:
        width, height = self._screen_size()
        if not image_path or not os.path.exists(image_path):
            if self.bg_label is not None:
                self.bg_label.destroy()
                self.bg_label = None
            return

        pil_image = Image.open(image_path)
        pil_image = pil_image.resize((width, height), Image.Resampling.LANCZOS)
        self._tk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(width, height))

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
