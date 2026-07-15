"""Teacher display preferences screen."""

from __future__ import annotations

from tkinter import END, filedialog, messagebox

import customtkinter as ctk

from app.data.election_store import ElectionStore
from app.ui.background_manager import BackgroundManager


class SettingsScreen:
    """Local display settings dialog — preserved from legacy application."""

    def __init__(
        self,
        root: ctk.CTk,
        store: ElectionStore,
        bg_manager: BackgroundManager,
        mode_state: dict,
    ) -> None:
        self.root = root
        self.store = store
        self.bg_manager = bg_manager
        self.mode_state = mode_state

    def open(self) -> None:
        app_data = self.store.data
        settings_tab = ctk.CTkToplevel(self.root)
        settings_tab.title("Settings")
        screen_h = self.root.winfo_screenheight()
        win_h = min(750, screen_h - 100)
        settings_tab.geometry(f"550x{win_h}")
        settings_tab.resizable(False, False)
        settings_tab.attributes("-topmost", True)

        scroll_container = ctk.CTkScrollableFrame(settings_tab, width=520, height=730)
        scroll_container.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(scroll_container, text="Adjust Preferences", font=("Arial", 18, "bold")).pack(pady=10)
        ctk.CTkLabel(
            scroll_container,
            text="Theme(Dark/Light)",
            font=("Arial", 12, "bold"),
            text_color="#3b7bb2",
        ).pack(anchor="w", pady=(10, 5))
        theme_frame = ctk.CTkFrame(scroll_container)
        theme_frame.pack(fill="x", pady=5)

        def dark_light_mode_switcher() -> None:
            if self.mode_state["mode"] == "dark":
                ctk.set_appearance_mode("light")
                self.mode_state["mode"] = "light"
            else:
                ctk.set_appearance_mode("dark")
                self.mode_state["mode"] = "dark"
            self.bg_manager.refresh_auto()

        switch_var = ctk.StringVar(value=self.mode_state["mode"])
        ctk.CTkSwitch(
            theme_frame,
            text="Light Mode / Dark Mode",
            command=dark_light_mode_switcher,
            variable=switch_var,
            onvalue="dark",
            offvalue="light",
        ).pack(anchor="w", padx=15, pady=10)

        def browse_light_bg() -> None:
            file_path = filedialog.askopenfilename(
                title="Select Light Mode Background",
                filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")],
            )
            if file_path:
                app_data["background_path_light"] = file_path
                self.store.save()
                self.bg_manager.refresh_auto()
                messagebox.showinfo("Success", "Light Mode background saved.", parent=settings_tab)

        ctk.CTkButton(
            theme_frame,
            text="🖼️ Choose Light Mode Background",
            fg_color="#e0e0e0",
            text_color="#000000",
            hover_color="#c0c0c0",
            command=browse_light_bg,
        ).pack(fill="x", padx=15, pady=5)

        def browse_dark_bg() -> None:
            file_path = filedialog.askopenfilename(
                title="Select Dark Mode Background",
                filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")],
            )
            if file_path:
                app_data["background_path_dark"] = file_path
                self.store.save()
                self.bg_manager.refresh_auto()
                messagebox.showinfo("Success", "Dark Mode background saved.", parent=settings_tab)

        ctk.CTkButton(
            theme_frame,
            text="🖼️ Choose Dark Mode Background",
            fg_color="#2b2b2b",
            text_color="#ffffff",
            hover_color="#1f1f1f",
            command=browse_dark_bg,
        ).pack(fill="x", padx=15, pady=5)

        def reset_to_basic_format() -> None:
            app_data["background_path_light"] = "assets/backgrounds/default_light_bg.png"
            app_data["background_path_dark"] = "assets/backgrounds/default_dark_bg.png"
            self.store.save()
            self.bg_manager.refresh_auto()
            messagebox.showinfo(
                "Success",
                "Themes restored back to default system layouts!",
                parent=settings_tab,
            )

        ctk.CTkButton(
            theme_frame,
            text="Reset to Default Theme (Remove Images)",
            fg_color="#a83232",
            hover_color="#7a2222",
            command=reset_to_basic_format,
        ).pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(scroll_container, text="Toggles", font=("Arial", 12, "bold"), text_color="#3b7bb2").pack(
            anchor="w", pady=(15, 5)
        )
        switch_frame = ctk.CTkFrame(scroll_container)
        switch_frame.pack(fill="x", pady=5)

        aspect_var = ctk.BooleanVar(value=app_data.get("aspect_ratio_fix", False))
        ctk.CTkSwitch(
            switch_frame,
            text="Aspect Ratio Adjustment (Fix Squished Images)",
            variable=aspect_var,
        ).pack(anchor="w", padx=15, pady=6)

        popup_var = ctk.BooleanVar(value=app_data.get("show_voting_popup", True))
        ctk.CTkSwitch(switch_frame, text="Voting Pop-up", variable=popup_var).pack(anchor="w", padx=15, pady=6)

        pop_img_var = ctk.BooleanVar(value=app_data.get("show_popup_images", True))
        ctk.CTkSwitch(switch_frame, text="Pop-up Images", variable=pop_img_var).pack(anchor="w", padx=15, pady=6)

        border_var = ctk.BooleanVar(value=app_data.get("show_image_borders", True))
        ctk.CTkSwitch(switch_frame, text="Image Borders", variable=border_var).pack(anchor="w", padx=15, pady=6)

        ctk.CTkLabel(
            scroll_container,
            text="Layout, Sizing & Typography",
            font=("Arial", 12, "bold"),
            text_color="#3b7bb2",
        ).pack(anchor="w", pady=(15, 5))
        dim_frame = ctk.CTkFrame(scroll_container)
        dim_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(dim_frame, text="Image Size:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        img_size_entry = ctk.CTkEntry(dim_frame, width=80)
        img_size_entry.insert(0, str(app_data.get("image_size", 140)))
        img_size_entry.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkLabel(dim_frame, text="Space Between Images:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        spacing_entry = ctk.CTkEntry(dim_frame, width=80)
        spacing_entry.insert(0, str(app_data.get("image_spacing", 20)))
        spacing_entry.grid(row=1, column=1, padx=10, pady=5)

        ctk.CTkLabel(dim_frame, text="Font Family:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        font_options = ["Arial", "Helvetica", "Times New Roman", "Courier", "Impact"]
        font_dropdown = ctk.CTkOptionMenu(dim_frame, values=font_options, width=120)
        font_dropdown.set(app_data.get("font_family", "Arial"))
        font_dropdown.grid(row=2, column=1, padx=10, pady=5)

        ctk.CTkLabel(dim_frame, text="Text Display Size:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        text_size_entry = ctk.CTkEntry(dim_frame, width=80)
        text_size_entry.insert(0, str(app_data.get("text_size", 16)))
        text_size_entry.grid(row=3, column=1, padx=10, pady=5)

        ctk.CTkLabel(dim_frame, text="Font Colour:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        color_map = {
            "White": "#FFFFFF",
            "Black": "#000000",
            "Gold": "#FFD700",
            "Red": "#DC143C",
            "Blue": "#4169E1",
            "Green": "#50C878",
        }
        color_dropdown = ctk.CTkOptionMenu(dim_frame, values=list(color_map.keys()), width=120)
        current_hex = app_data.get("font_color", "#FFFFFF")
        current_name = "White"
        for name, hex_code in color_map.items():
            if hex_code == current_hex:
                current_name = name
                break
        color_dropdown.set(current_name)
        color_dropdown.grid(row=4, column=1, padx=10, pady=5)

        def trigger_auto_config() -> None:
            screen_w = self.root.winfo_screenwidth()
            img_size_entry.delete(0, END)
            img_size_entry.insert(0, str(int(screen_w * 0.08)))
            messagebox.showinfo(
                "Auto-Configuration",
                f"Optimized for screen width: {screen_w}px.",
                parent=settings_tab,
            )

        ctk.CTkButton(
            scroll_container,
            text="Auto-Configuration",
            fg_color="#2b5982",
            command=trigger_auto_config,
        ).pack(fill="x", pady=(15, 5))

        def save_settings_action() -> None:
            try:
                app_data["image_size"] = int(img_size_entry.get())
                app_data["image_spacing"] = int(spacing_entry.get())
                app_data["font_family"] = font_dropdown.get()
                app_data["text_size"] = int(text_size_entry.get())
                app_data["font_color"] = color_map.get(color_dropdown.get(), "#FFFFFF")
                app_data["aspect_ratio_fix"] = aspect_var.get()
                app_data["show_voting_popup"] = popup_var.get()
                app_data["show_popup_images"] = pop_img_var.get()
                app_data["show_image_borders"] = border_var.get()
                self.store.save()
                self.bg_manager.refresh_auto()
                messagebox.showinfo("Saved", "Preferences written successfully.", parent=settings_tab)
                settings_tab.destroy()
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Please verify sizes and spacing fields are numbers.",
                    parent=settings_tab,
                )

        ctk.CTkButton(
            scroll_container,
            text="Save Changes",
            font=("Arial", 14, "bold"),
            fg_color="#1e5228",
            command=save_settings_action,
        ).pack(fill="x", pady=15)
