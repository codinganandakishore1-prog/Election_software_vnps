"""Node-operator administration panel (read-only election data)."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
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
        on_config_installed: Callable[[], None] | None = None,
    ) -> None:
        self.root = root
        self.store = store
        self.config_service = config_service
        self.sync_manager = sync_manager
        self.diagnostics_service = diagnostics_service
        self.on_config_installed = on_config_installed
        self._dashboard: ctk.CTkToplevel | None = None
        self._candidates_host: ctk.CTkFrame | None = None
        self._meta_label: ctk.CTkLabel | None = None
        self._thumb_refs: list[ctk.CTkImage] = []

    def open(self) -> None:
        dashboard = ctk.CTkToplevel(self.root)
        self._dashboard = dashboard
        dashboard.title("Node Administration")
        screen_w = dashboard.winfo_screenwidth()
        screen_h = dashboard.winfo_screenheight()
        win_w, win_h = min(980, screen_w - 80), min(820, screen_h - 80)
        dashboard.geometry(f"{win_w}x{win_h}")
        dashboard.transient(self.root)
        dashboard.lift()
        dashboard.focus_force()
        dashboard.attributes("-topmost", True)
        dashboard.after(150, lambda: dashboard.attributes("-topmost", False) if dashboard.winfo_exists() else None)

        header = ctk.CTkFrame(dashboard, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 6))

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            title_col,
            text="Node Administration",
            font=("Arial", 20, "bold"),
        ).pack(anchor="w")
        self._meta_label = ctk.CTkLabel(
            title_col,
            text="",
            font=("Arial", 12),
            text_color="#9ca3af",
            anchor="w",
        )
        self._meta_label.pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            header,
            text="Logout",
            width=100,
            fg_color="#a83232",
            hover_color="#7a2222",
            command=dashboard.destroy,
        ).pack(side="right")

        actions = ctk.CTkFrame(dashboard, fg_color="transparent")
        actions.pack(fill="x", padx=16, pady=(4, 10))

        action_specs = (
            ("Download Election", self._open_download_dialog),
            ("Sync Status", self._open_sync_dialog),
            ("Diagnostics", self._open_diagnostics_dialog),
            ("Node Config", self._open_node_config_dialog),
            ("Security PIN", self._open_security_dialog),
        )
        for label, command in action_specs:
            ctk.CTkButton(
                actions,
                text=label,
                height=34,
                fg_color="#2b2b2b",
                hover_color="#3a3a3a",
                command=command,
            ).pack(side="left", padx=(0, 8))

        body = ctk.CTkFrame(dashboard, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        ctk.CTkLabel(
            body,
            text="Candidates by Position",
            font=("Arial", 15, "bold"),
            text_color="#3b7bb2",
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        self._candidates_host = ctk.CTkFrame(body, fg_color="transparent")
        self._candidates_host.pack(fill="both", expand=True)
        self._refresh_candidate_view()

    def _election_meta_text(self) -> str:
        election_id = self.store.data.get("election_id") or "—"
        version = self.store.data.get("election_version") or 0
        last = self.store.data.get("last_download_at") or "Never"
        return f"Election: {election_id}   ·   Version: {version}   ·   Last download: {last}"

    def _refresh_candidate_view(self) -> None:
        if self._meta_label is not None:
            self._meta_label.configure(text=self._election_meta_text())
        if self._candidates_host is None:
            return

        for child in self._candidates_host.winfo_children():
            child.destroy()
        self._thumb_refs.clear()

        scroll = ctk.CTkScrollableFrame(self._candidates_host, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        candidates = self.store.candidates
        positions = self.store.positions
        if not candidates:
            ctk.CTkLabel(
                scroll,
                text="No election downloaded yet. Use Download Election to load candidates.",
                font=("Arial", 14),
                text_color="#9ca3af",
            ).pack(pady=48)
            return

        for position in positions:
            matching = [c for c in candidates if c.get("position") == position]
            if not matching:
                continue

            section = ctk.CTkFrame(scroll, fg_color="#1f2937", corner_radius=8)
            section.pack(fill="x", pady=(0, 12), padx=2)

            ctk.CTkLabel(
                section,
                text=position,
                font=("Arial", 14, "bold"),
                text_color="#3b7bb2",
                anchor="w",
            ).pack(anchor="w", padx=14, pady=(12, 6))

            for cand in matching:
                row = ctk.CTkFrame(section, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=6)

                thumb = ctk.CTkLabel(
                    row,
                    text="",
                    width=48,
                    height=48,
                    fg_color="#374151",
                    corner_radius=6,
                )
                thumb.pack(side="left", padx=(0, 12))

                img_path = self.store.resolve_path(cand.get("image_path", ""))
                if img_path and os.path.exists(img_path):
                    try:
                        p_img = Image.open(img_path).resize((48, 48), Image.Resampling.LANCZOS)
                        tk_thumb = ctk.CTkImage(light_image=p_img, dark_image=p_img, size=(48, 48))
                        thumb.configure(image=tk_thumb)
                        self._thumb_refs.append(tk_thumb)
                    except Exception:
                        thumb.configure(text="—")
                else:
                    thumb.configure(text="—")

                details = ctk.CTkFrame(row, fg_color="transparent")
                details.pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(
                    details,
                    text=cand.get("name", "Unknown"),
                    font=("Arial", 13, "bold"),
                    anchor="w",
                ).pack(anchor="w")

                class_text = cand.get("candidate_class") or "—"
                section_text = cand.get("candidate_section") or "—"
                ctk.CTkLabel(
                    details,
                    text=f"Class {class_text} · Section {section_text}",
                    font=("Arial", 12),
                    text_color="#9ca3af",
                    anchor="w",
                ).pack(anchor="w")

    def _close_dialog(self, win: ctk.CTkToplevel) -> None:
        try:
            win.grab_release()
        except Exception:
            pass
        if win.winfo_exists():
            win.destroy()
        if self._dashboard is not None and self._dashboard.winfo_exists():
            self._dashboard.lift()
            self._dashboard.focus_force()

    def _dialog(self, title: str, width: int = 460, height: int = 420) -> ctk.CTkToplevel:
        parent = self._dashboard or self.root
        win = ctk.CTkToplevel(parent)
        win.title(title)
        win.geometry(f"{width}x{height}")
        win.resizable(False, False)
        win.transient(parent)
        win.protocol("WM_DELETE_WINDOW", lambda: self._close_dialog(win))

        def bring_forward() -> None:
            if not win.winfo_exists():
                return
            win.lift()
            win.focus_force()
            win.attributes("-topmost", True)
            try:
                win.grab_set()
            except Exception:
                pass
            win.after(200, lambda: win.attributes("-topmost", False) if win.winfo_exists() else None)

        win.after(20, bring_forward)
        return win

    def _field_label(self, parent: ctk.CTkFrame, text: str) -> None:
        ctk.CTkLabel(parent, text=text, font=("Arial", 12, "bold"), anchor="w").pack(
            anchor="w", pady=(0, 4)
        )

    def _prefilled_entry(
        self,
        parent: ctk.CTkFrame,
        value: str,
        *,
        show: str | None = None,
        height: int = 36,
    ) -> ctk.CTkEntry:
        kwargs: dict = {"height": height}
        if show is not None:
            kwargs["show"] = show
        entry = ctk.CTkEntry(parent, **kwargs)
        if value:
            entry.insert(0, value)
        entry.pack(fill="x", pady=(0, 12))
        return entry

    def _open_download_dialog(self) -> None:
        win = self._dialog("Download Election", width=500, height=420)
        body = ctk.CTkFrame(win, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(
            body,
            text="Download from server or import a published package.",
            text_color="#9ca3af",
            anchor="w",
        ).pack(anchor="w", pady=(0, 14))

        default_election = str(self.store.data.get("election_id") or "")
        self._field_label(body, "Election ID")
        election_entry = self._prefilled_entry(body, default_election)

        self._field_label(body, "Node token (optional)")
        token_entry = self._prefilled_entry(body, "")

        def download_from_server() -> None:
            election_id = election_entry.get().strip()
            if not election_id:
                messagebox.showerror("Error", "Election ID is required.", parent=win)
                return
            try:
                win.config(cursor="watch")
                win.update_idletasks()
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
                    parent=win,
                )
                self._refresh_candidate_view()
                if self.on_config_installed:
                    self.on_config_installed()
                self._close_dialog(win)
            except Exception as exc:
                messagebox.showerror("Download Failed", str(exc), parent=win)
            finally:
                if win.winfo_exists():
                    win.config(cursor="")

        def import_local_package() -> None:
            win.attributes("-topmost", False)
            path = filedialog.askopenfilename(parent=win, filetypes=[("ZIP package", "*.zip")])
            if not path:
                win.after(20, lambda: win.lift() if win.winfo_exists() else None)
                return
            try:
                result = self.store.install_config_package(path)
                self.store.update(last_download_at=time.strftime("%Y-%m-%d %H:%M:%S"))
                messagebox.showinfo(
                    "Success",
                    f"Installed package with {result.get('candidates', 0)} candidates.",
                    parent=win,
                )
                self._refresh_candidate_view()
                if self.on_config_installed:
                    self.on_config_installed()
                self._close_dialog(win)
            except Exception as exc:
                messagebox.showerror("Import Failed", str(exc), parent=win)

        ctk.CTkButton(
            body,
            text="Download Election",
            height=36,
            fg_color="#1e5228",
            hover_color="#163d1e",
            command=download_from_server,
        ).pack(fill="x", pady=(0, 8))

        ctk.CTkButton(
            body,
            text="Import Local Package",
            height=36,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            command=import_local_package,
        ).pack(fill="x")

        ctk.CTkLabel(
            body,
            text="Accepts a published .zip configuration package.",
            font=("Arial", 11),
            text_color="#6b7280",
            anchor="w",
        ).pack(anchor="w", pady=(8, 0))

    def _open_sync_dialog(self) -> None:
        win = self._dialog("Synchronization Status", width=500, height=380)
        body = ctk.CTkFrame(win, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=18)

        status_box = ctk.CTkTextbox(body, height=240, wrap="word", font=("Arial", 13))
        status_box.pack(fill="both", expand=True, pady=(0, 12))
        status_box.configure(state="disabled")

        def refresh_sync_status() -> None:
            status = self.sync_manager.status()
            text = (
                f"Queue size: {status['queue_size']}\n"
                f"Primary queue: {status.get('primary_queue_size', status['queue_size'])}\n"
                f"Retry queue: {status.get('retry_queue_size', 0)}\n"
                f"Uploads enabled: {'Yes' if status.get('uploads_enabled') else 'No'}\n"
                f"Running: {'Yes' if status['running'] else 'No'}\n"
                f"Last sync: {status['last_sync_at'] or 'Never'}\n"
                f"Last error: {status['last_error'] or 'None'}"
            )
            status_box.configure(state="normal")
            status_box.delete("1.0", "end")
            status_box.insert("1.0", text)
            status_box.configure(state="disabled")

        ctk.CTkButton(
            body,
            text="Refresh Status",
            height=36,
            fg_color="#2b2b2b",
            hover_color="#3a3a3a",
            command=refresh_sync_status,
        ).pack(fill="x")
        refresh_sync_status()

    def _open_diagnostics_dialog(self) -> None:
        win = self._dialog("Diagnostics", width=560, height=480)
        body = ctk.CTkFrame(win, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=18)

        scroll = ctk.CTkScrollableFrame(body, label_text="System Health")
        scroll.pack(fill="both", expand=True)

        for key, value in self.diagnostics_service.collect().items():
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(
                row,
                text=f"{key}",
                width=180,
                anchor="w",
                font=("Arial", 12, "bold"),
            ).pack(side="left", padx=(4, 8))
            ctk.CTkLabel(
                row,
                text=str(value),
                anchor="w",
                wraplength=300,
                justify="left",
            ).pack(side="left", fill="x", expand=True)

    def _open_node_config_dialog(self) -> None:
        win = self._dialog("Node Configuration", width=500, height=420)
        body = ctk.CTkFrame(win, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=18)

        default_node_id = str(self.store.data.get("node_id") or settings.node_id or "")
        default_secret = str(self.store.data.get("node_secret") or settings.node_secret or "")
        default_url = str(
            self.store.data.get("website_url") or settings.website_url or "http://localhost:8000"
        )

        self._field_label(body, "Node ID")
        node_id_entry = self._prefilled_entry(body, default_node_id)

        self._field_label(body, "Node Secret")
        node_secret_entry = self._prefilled_entry(body, default_secret, show="*")

        self._field_label(body, "Website / API URL")
        website_entry = self._prefilled_entry(body, default_url)

        def save_node_config() -> None:
            self.store.update(
                node_id=node_id_entry.get().strip(),
                node_secret=node_secret_entry.get().strip(),
                website_url=website_entry.get().strip(),
            )
            messagebox.showinfo("Success", "Node configuration saved.", parent=win)
            self._close_dialog(win)

        ctk.CTkButton(
            body,
            text="Save Node Configuration",
            height=36,
            fg_color="#1e5228",
            hover_color="#163d1e",
            command=save_node_config,
        ).pack(fill="x")

    def _open_security_dialog(self) -> None:
        win = self._dialog("Security PIN", width=460, height=380)
        body = ctk.CTkFrame(win, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=18)

        current_pin = str(self.store.data.get("password") or "1234")

        self._field_label(body, "Current PIN")
        old_p = self._prefilled_entry(body, current_pin, show="*")

        self._field_label(body, "New PIN")
        new_p = self._prefilled_entry(body, "")

        self._field_label(body, "Verify New PIN")
        ver_p = self._prefilled_entry(body, "")

        def update_password_action() -> None:
            if old_p.get() != self.store.data.get("password", "1234"):
                messagebox.showerror("Error", "Current password mismatch.", parent=win)
                return
            if not new_p.get():
                messagebox.showerror("Error", "New PIN cannot be empty.", parent=win)
                return
            if new_p.get() != ver_p.get():
                messagebox.showerror("Error", "New passwords mismatch.", parent=win)
                return
            self.store.update(password=new_p.get())
            messagebox.showinfo("Success", "PIN updated.", parent=win)
            self._close_dialog(win)

        ctk.CTkButton(
            body,
            text="Update Security PIN",
            height=36,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            command=update_password_action,
        ).pack(fill="x")

