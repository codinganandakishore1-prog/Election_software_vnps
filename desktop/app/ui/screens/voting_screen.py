"""Voting workflow screen."""

from __future__ import annotations

import os
import time

import customtkinter as ctk
from PIL import Image

from app.data.election_store import ElectionStore
from app.services.vote_service import VoteService
from app.ui.background_manager import BackgroundManager
from app.ui.components.vote_toast import show_vote_notification


class VotingScreen:
    """Fullscreen ballot flow — preserves legacy workflow and animations."""

    def __init__(
        self,
        root: ctk.CTk,
        store: ElectionStore,
        vote_service: VoteService,
        bg_manager: BackgroundManager,
        next_vote_btn: ctk.CTkButton,
    ) -> None:
        self.root = root
        self.store = store
        self.vote_service = vote_service
        self.bg_manager = bg_manager
        self.next_vote_btn = next_vote_btn
        self.ballot_frame: ctk.CTkFrame | None = None
        self.current_post_index = 0

    def start_session(self) -> None:
        self.next_vote_btn.configure(border_width=2, fg_color="#1a1a1a", border_color="#111111")
        self.root.update()
        time.sleep(0.1)

        self.bg_manager.refresh_voting()
        self.root.update_idletasks()
        if self.bg_manager.bg_label:
            self.bg_manager.bg_label.lower()

        self.current_post_index = 0
        self.next_vote_btn.place_forget()

        self.ballot_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.ballot_frame.place(relx=0.5, rely=0.5, anchor="center")
        self._render_current_ballot_post()

    def _render_current_ballot_post(self) -> None:
        if self.ballot_frame is None:
            return

        for widget in self.ballot_frame.winfo_children():
            widget.destroy()

        positions = self.store.positions
        if self.current_post_index >= len(positions):
            self.ballot_frame.destroy()
            self.ballot_frame = None
            self.bg_manager.refresh_welcome()
            self.next_vote_btn.place(relx=0.49, rely=0.70, anchor="nw")
            return

        app_data = self.store.data
        target_post = positions[self.current_post_index]
        selected_font = app_data.get("font_family", "Arial")
        selected_size = app_data.get("text_size", 16)
        selected_color = app_data.get("font_color", "#FFFFFF")
        custom_spacing = app_data.get("image_spacing", 20)
        custom_img_size = app_data.get("image_size", 140)
        border_thickness = 2 if app_data.get("show_image_borders", True) else 0

        header = ctk.CTkLabel(
            self.ballot_frame,
            text=f"VOTE FOR YOUR: {target_post.upper()}",
            font=(selected_font, int(selected_size * 1.5), "bold"),
            text_color=selected_color,
        )
        header.pack(pady=30)

        cards_container = ctk.CTkFrame(self.ballot_frame, fg_color="transparent")
        cards_container.pack()

        matching_candidates = [c for c in self.store.candidates if c.get("position") == target_post]
        if not matching_candidates:
            self.current_post_index += 1
            self._render_current_ballot_post()
            return

        for cand in matching_candidates:
            card_width = custom_img_size + 80
            card_height = custom_img_size + 200

            card = ctk.CTkFrame(
                cards_container,
                width=card_width,
                height=card_height,
                border_width=border_thickness,
                border_color="#3a3a3a",
            )
            card.pack(side="left", padx=custom_spacing, pady=10)
            card.pack_propagate(False)

            img_path = self.store.resolve_path(cand.get("image_path", ""))
            if img_path and os.path.exists(img_path):
                try:
                    p_img = Image.open(img_path)
                    if app_data.get("aspect_ratio_fix", False):
                        calculated_w = int(custom_img_size * 0.85)
                        p_img = p_img.resize((calculated_w, custom_img_size), Image.Resampling.LANCZOS)
                        ctk_img = ctk.CTkImage(
                            light_image=p_img,
                            dark_image=p_img,
                            size=(calculated_w, custom_img_size),
                        )
                    else:
                        p_img = p_img.resize((custom_img_size, custom_img_size), Image.Resampling.LANCZOS)
                        ctk_img = ctk.CTkImage(
                            light_image=p_img,
                            dark_image=p_img,
                            size=(custom_img_size, custom_img_size),
                        )
                    img_label = ctk.CTkLabel(card, text="", image=ctk_img)
                except Exception:
                    img_label = ctk.CTkLabel(
                        card,
                        text="[ Image Error ]",
                        width=custom_img_size,
                        height=custom_img_size,
                        fg_color="#2b2b2b",
                    )
            else:
                img_label = ctk.CTkLabel(
                    card,
                    text="[ No Image ]",
                    width=custom_img_size,
                    height=custom_img_size,
                    fg_color="#2b2b2b",
                )
            img_label.pack(pady=15)

            name_label = ctk.CTkLabel(
                card,
                text=cand.get("name", "Unknown"),
                font=(selected_font, selected_size, "bold"),
                text_color=selected_color,
                wraplength=card_width - 20,
            )
            name_label.pack(pady=2)

            class_text = (
                f"Class: {cand.get('candidate_class', '')} - "
                f"{cand.get('candidate_section', '').upper()}"
            )
            metadata_label = ctk.CTkLabel(
                card,
                text=class_text,
                font=(selected_font, int(selected_size * 0.8)),
                text_color="#888888",
            )
            metadata_label.pack(pady=2)

            indicator_dot = ctk.CTkLabel(
                card,
                text="",
                width=18,
                height=18,
                fg_color="#4a1515",
                corner_radius=9,
            )
            indicator_dot.pack(pady=5)

            ctk.CTkButton(
                card,
                text="VOTE",
                font=(selected_font, int(selected_size * 0.9), "bold"),
                fg_color="#1e5228",
                hover_color="#153b1d",
                command=lambda c=cand, dot=indicator_dot: self._record_vote_action(c, dot),
            ).pack(pady=15, side="bottom")

    def _record_vote_action(self, candidate_data: dict, target_dot: ctk.CTkLabel) -> None:
        target_dot.configure(fg_color="#FF0000")
        if self.store.data.get("show_voting_popup", True):
            show_vote_notification(self.root, candidate_data["name"])
        self.vote_service.record_vote(candidate_data)
        self.root.after(200, self._progress_to_next_ballot_stage)

    def _progress_to_next_ballot_stage(self) -> None:
        self.current_post_index += 1
        self._render_current_ballot_post()

    def get_ballot_frame(self) -> ctk.CTkFrame | None:
        return self.ballot_frame
