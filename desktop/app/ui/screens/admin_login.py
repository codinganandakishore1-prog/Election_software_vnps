"""Administrator login dialog."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from app.data.election_store import ElectionStore


class AdminLoginScreen:
    """Password gate for node-operator administration."""

    def __init__(self, root: ctk.CTk, store: ElectionStore, on_success) -> None:
        self.root = root
        self.store = store
        self.on_success = on_success

    def open(self) -> None:
        login_window = ctk.CTkToplevel(self.root)
        login_window.title("Admin Verification")
        login_window.geometry("380x240")
        login_window.resizable(False, False)
        login_window.transient(self.root)

        def bring_forward() -> None:
            if not login_window.winfo_exists():
                return
            login_window.lift()
            login_window.focus_force()
            login_window.attributes("-topmost", True)
            try:
                login_window.grab_set()
            except Exception:
                pass
            login_window.after(
                200,
                lambda: login_window.attributes("-topmost", False)
                if login_window.winfo_exists()
                else None,
            )

        login_window.after(20, bring_forward)

        ctk.CTkLabel(login_window, text="Admin Password", font=("Arial", 14, "bold")).pack(
            pady=(20, 6)
        )
        password_entry = ctk.CTkEntry(login_window, show="*", width=260, height=36)
        password_entry.pack(pady=6)
        password_entry.focus_set()

        def attempt_login() -> None:
            if password_entry.get() == self.store.data.get("password", "1234"):
                try:
                    login_window.grab_release()
                except Exception:
                    pass
                login_window.destroy()
                self.on_success()
            else:
                messagebox.showerror("Access Denied", "Incorrect password entry.", parent=login_window)

        ctk.CTkButton(login_window, text="Unlock Controls", command=attempt_login).pack(pady=16)
        login_window.bind("<Return>", lambda _event: attempt_login())
