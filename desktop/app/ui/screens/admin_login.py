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
        login_window.geometry("350x200")
        login_window.resizable(False, False)
        login_window.attributes("-topmost", True)

        ctk.CTkLabel(login_window, text="Enter Admin Password:", font=("Arial", 14)).pack(pady=15)
        password_entry = ctk.CTkEntry(login_window, show="*")
        password_entry.pack(pady=5)

        def attempt_login() -> None:
            if password_entry.get() == self.store.data.get("password", "1234"):
                login_window.destroy()
                self.on_success()
            else:
                messagebox.showerror("Access Denied", "Incorrect password entry.", parent=login_window)

        ctk.CTkButton(login_window, text="Unlock Controls", command=attempt_login).pack(pady=15)
