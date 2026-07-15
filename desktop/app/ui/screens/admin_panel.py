"""Node-operator administration panel (read-only election data)."""

from __future__ import annotations

import os
import time
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from app.config.settings import settings
from app.data.election_store import ElectionStore
from app.health.diagnostics import DiagnosticsService
from app.services.config_service import ConfigService
from app.sync.sync_manager import SyncManager


class AdminPanelScreen:
    """Simplified administrator panel for node operations."""

    def __init__(
        self,
        root: ctk.CTk,
        store: ElectionStore,
        config_service: ConfigService,
        sync_manager: SyncManager,
        diagnostics_service: DiagnosticsService,
    ) -> None:
        self.root = root
        self.store = store
        self.config_service = config_service
        self.sync_manager = sync_manager
        self.diagnostics_service = diagnostics_service

    def open(self) -> None:
        dashboard = ctk.CTkToplevel(self.root)
        dashboard.title("Node Administration")
        screen_height = dashboard.winfo_screenheight()
        win_w, win_h = 900, min(800, screen_height - 100)
        dashboard.geometry(f"{win_w}x{win_h}")
        dashboard.attributes("-topmost", True)

        left_container = ctk.CTkFrame(dashboard, width=360)
        left_container.pack(side="left", fill="both", padx=10, pady=10)

        left_scroll = ctk.CTkScrollableFrame(left_container, label_text="Node Operations", fg_color="transparent")
        left_scroll.pack(fill="both", expand=True)

        self._build_security_section(left_scroll)
        self._build_download_section(left_scroll, dashboard)
        self._build_node_config_section(left_scroll)
        self._build_database_section(left_scroll)
        self._build_sync_section(left_scroll)

        right_container = ctk.CTkFrame(dashboard)
        right_container.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self._build_diagnostics_section(right_container)
        self._build_view_election_section(right_container)

        footer = ctk.CTkFrame(dashboard, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=20, pady=10)
        ctk.CTkButton(
            footer,
            text="Logout",
            fg_color="#a83232",
            hover_color="#7a2222",
            command=dashboard.destroy,
        ).pack(side="right")

    def _section_label(self, parent, text: str) -> None:
        ctk.CTkLabel(parent, text=text, font=("Arial", 13, "bold"), text_color="#3b7bb2").pack(
            pady=(15, 5), anchor="w"
        )

    def _build_security_section(self, parent) -> None:
        self._section_label(parent, "Security Settings")
        sec_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        sec_frame.pack(fill="x", padx=5, pady=5)

        old_p = ctk.CTkEntry(sec_frame, placeholder_text="Current PIN", show="*")
        old_p.pack(fill="x", padx=10, pady=5)
        new_p = ctk.CTkEntry(sec_frame, placeholder_text="New PIN", show="*")
        new_p.pack(fill="x", padx=10, pady=2)
        ver_p = ctk.CTkEntry(sec_frame, placeholder_text="Verify New PIN", show="*")
        ver_p.pack(fill="x", padx=10, pady=2)

        def update_password_action() -> None:
            if old_p.get() != self.store.data.get("password", "1234"):
                messagebox.showerror("Error", "Current password mismatch.")
                return
            if new_p.get() != ver_p.get():
                messagebox.showerror("Error", "New passwords mismatch.")
                return
            self.store.update(password=new_p.get())
            messagebox.showinfo("Success", "PIN updated.")

        ctk.CTkButton(
            sec_frame,
            text="Update Security PIN",
            height=28,
            fg_color="#4a4a4a",
            command=update_password_action,
        ).pack(fill="x", padx=10, pady=10)

    def _build_download_section(self, parent, dashboard) -> None:
        self._section_label(parent, "Configuration Download")
        download_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        download_frame.pack(fill="x", padx=5, pady=5)

        election_entry = ctk.CTkEntry(download_frame, placeholder_text="Election ID")
        election_entry.insert(0, self.store.data.get("election_id", ""))
        election_entry.pack(fill="x", padx=10, pady=8)

        token_entry = ctk.CTkEntry(download_frame, placeholder_text="Node token (optional)")
        token_entry.pack(fill="x", padx=10, pady=4)

        def download_from_server() -> None:
            election_id = election_entry.get().strip()
            if not election_id:
                messagebox.showerror("Error", "Election ID is required.")
                return
            try:
                dashboard.config(cursor="watch")
                dashboard.update_idletasks()
                result = self.config_service.download_election(
                    election_id,
                    token=token_entry.get().strip() or None,
                )
                self.store.update(
                    election_id=election_id,
                    last_download_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                    election_version=result.get("version", 0),
                )
                messagebox.showinfo(
                    "Success",
                    f"Downloaded election v{result.get('version', 0)} "
                    f"({result.get('candidates', 0)} candidates).",
                )
            except Exception as exc:
                messagebox.showerror("Download Failed", str(exc))
            finally:
                dashboard.config(cursor="")

        def import_local_package() -> None:
            path = filedialog.askopenfilename(filetypes=[("ZIP package", "*.zip")])
            if not path:
                return
            try:
                result = self.store.install_config_package(path)
                self.store.update(last_download_at=time.strftime("%Y-%m-%d %H:%M:%S"))
                messagebox.showinfo(
                    "Success",
                    f"Installed package with {result.get('candidates', 0)} candidates.",
                )
            except Exception as exc:
                messagebox.showerror("Import Failed", str(exc))

        ctk.CTkButton(
            download_frame,
            text="Download Election",
            height=28,
            fg_color="#1e5228",
            command=download_from_server,
        ).pack(fill="x", padx=10, pady=4)
        ctk.CTkButton(
            download_frame,
            text="Import Local Package (.zip)",
            height=28,
            fg_color="#4a4a4a",
            command=import_local_package,
        ).pack(fill="x", padx=10, pady=(0, 8))

    def _build_node_config_section(self, parent) -> None:
        self._section_label(parent, "Node Configuration")
        node_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        node_frame.pack(fill="x", padx=5, pady=5)

        node_id_entry = ctk.CTkEntry(node_frame, placeholder_text="Node ID")
        node_id_entry.insert(0, self.store.data.get("node_id", settings.node_id))
        node_id_entry.pack(fill="x", padx=10, pady=4)

        node_secret_entry = ctk.CTkEntry(node_frame, placeholder_text="Node Secret", show="*")
        node_secret_entry.insert(0, self.store.data.get("node_secret", settings.node_secret))
        node_secret_entry.pack(fill="x", padx=10, pady=4)

        website_entry = ctk.CTkEntry(node_frame, placeholder_text="Website URL")
        website_entry.insert(0, self.store.data.get("website_url", settings.website_url))
        website_entry.pack(fill="x", padx=10, pady=4)

        def save_node_config() -> None:
            self.store.update(
                node_id=node_id_entry.get().strip(),
                node_secret=node_secret_entry.get().strip(),
                website_url=website_entry.get().strip(),
            )
            messagebox.showinfo("Success", "Node configuration saved.")

        ctk.CTkButton(node_frame, text="Save Node Configuration", command=save_node_config).pack(
            fill="x", padx=10, pady=8
        )

    def _build_database_section(self, parent) -> None:
        self._section_label(parent, "Local Database Settings")
        db_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        db_frame.pack(fill="x", padx=5, pady=5)

        info = (
            f"Engine: {settings.local_db_engine}\n"
            f"Path/Host: {settings.local_db_path if settings.local_db_engine == 'sqlite' else settings.local_db_host}"
        )
        ctk.CTkLabel(db_frame, text=info, justify="left").pack(anchor="w", padx=10, pady=8)
        ctk.CTkLabel(
            db_frame,
            text="Database connection is configured via environment variables (.env).",
            text_color="#888888",
            wraplength=300,
            justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 8))

    def _build_sync_section(self, parent) -> None:
        self._section_label(parent, "Synchronization Status")
        sync_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        sync_frame.pack(fill="x", padx=5, pady=5)

        self.sync_status_label = ctk.CTkLabel(sync_frame, text="", justify="left")
        self.sync_status_label.pack(anchor="w", padx=10, pady=8)

        def refresh_sync_status() -> None:
            status = self.sync_manager.status()
            self.sync_status_label.configure(
                text=(
                    f"Queue size: {status['queue_size']}\n"
                    f"Primary queue: {status.get('primary_queue_size', status['queue_size'])}\n"
                    f"Retry queue: {status.get('retry_queue_size', 0)}\n"
                    f"Uploads enabled: {'Yes' if status.get('uploads_enabled') else 'No'}\n"
                    f"Running: {'Yes' if status['running'] else 'No'}\n"
                    f"Last sync: {status['last_sync_at'] or 'Never'}\n"
                    f"Last error: {status['last_error'] or 'None'}"
                )
            )

        ctk.CTkButton(sync_frame, text="Refresh Status", command=refresh_sync_status).pack(
            fill="x", padx=10, pady=(0, 8)
        )
        refresh_sync_status()

    def _build_diagnostics_section(self, parent) -> None:
        ctk.CTkLabel(parent, text="Diagnostics", font=("Arial", 16, "bold"), text_color="#3b7bb2").pack(
            anchor="w", pady=(5, 10)
        )
        diag_scroll = ctk.CTkScrollableFrame(parent, height=220, label_text="System Health")
        diag_scroll.pack(fill="x", padx=5, pady=5)

        for key, value in self.diagnostics_service.collect().items():
            row = ctk.CTkFrame(diag_scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{key}:", width=160, anchor="w", font=("Arial", 12, "bold")).pack(
                side="left", padx=5
            )
            ctk.CTkLabel(row, text=value, anchor="w").pack(side="left", fill="x", expand=True)

    def _build_view_election_section(self, parent) -> None:
        ctk.CTkLabel(
            parent,
            text="Downloaded Election (Read-Only)",
            font=("Arial", 16, "bold"),
            text_color="#3b7bb2",
        ).pack(anchor="w", pady=(15, 10))

        scroll_view = ctk.CTkScrollableFrame(parent, label_text="Candidates by Position")
        scroll_view.pack(fill="both", expand=True, padx=5, pady=5)

        candidates = self.store.candidates
        positions = self.store.positions
        if not candidates:
            ctk.CTkLabel(
                scroll_view,
                text="No downloaded election data. Use Configuration Download.",
                font=("Arial", 14, "italic"),
            ).pack(pady=40)
            return

        for pos in positions:
            matching = [c for c in candidates if c.get("position") == pos]
            if not matching:
                continue
            section_frame = ctk.CTkFrame(scroll_view, fg_color="#1f2937", corner_radius=6)
            section_frame.pack(fill="x", pady=(10, 5), padx=5)
            ctk.CTkLabel(
                section_frame,
                text=f"POSITION: {pos.upper()}",
                font=("Arial", 13, "bold"),
                text_color="#3b7bb2",
            ).pack(anchor="w", padx=10, pady=6)

            for cand in matching:
                cand_row = ctk.CTkFrame(scroll_view, fg_color="transparent")
                cand_row.pack(fill="x", pady=4, padx=10)
                thumb_label = ctk.CTkLabel(
                    cand_row,
                    text="[No Photo]",
                    width=40,
                    height=40,
                    fg_color="#374151",
                    corner_radius=4,
                )
                thumb_label.pack(side="left", padx=(5, 15))
                img_path = self.store.resolve_path(cand.get("image_path", ""))
                if img_path and os.path.exists(img_path):
                    try:
                        p_img = Image.open(img_path).resize((40, 40), Image.Resampling.LANCZOS)
                        tk_thumb = ctk.CTkImage(light_image=p_img, dark_image=p_img, size=(40, 40))
                        thumb_label.configure(image=tk_thumb, text="")
                        thumb_label.image = tk_thumb  # type: ignore[attr-defined]
                    except Exception:
                        pass
                info_text = (
                    f"👤 Name: {cand.get('name', 'Unknown')}   |   "
                    f"Class: {cand.get('candidate_class', 'N/A')} - "
                    f"Section: {cand.get('candidate_section', 'N/A')}"
                )
                ctk.CTkLabel(cand_row, text=info_text, font=("Arial", 13)).pack(side="left", anchor="w")
                ctk.CTkFrame(scroll_view, height=1, fg_color="#374151").pack(fill="x", padx=15, pady=2)
