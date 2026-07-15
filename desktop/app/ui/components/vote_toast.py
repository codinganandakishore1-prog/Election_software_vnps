"""Vote toast notification component."""

from __future__ import annotations

import customtkinter as ctk


def show_vote_notification(root: ctk.CTk, candidate_name: str) -> None:
    """Display the existing vote confirmation toast and bell sound."""
    toast = ctk.CTkFrame(
        root,
        corner_radius=10,
        fg_color="#1e5228",
        border_width=2,
        border_color="#50C878",
    )
    toast.place(relx=0.98, rely=0.05, anchor="ne")

    label = ctk.CTkLabel(
        toast,
        text=f"Voted for: {candidate_name}",
        font=("Arial", 14, "bold"),
        text_color="white",
        padx=20,
        pady=10,
    )
    label.pack()

    try:
        root.bell()
    except Exception:
        pass

    root.after(2000, toast.destroy)
