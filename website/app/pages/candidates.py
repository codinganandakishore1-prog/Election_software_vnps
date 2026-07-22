"""Candidate management page with desktop-style photo editor."""

from __future__ import annotations

from typing import Any

from nicegui import events, ui
from PIL import Image

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.services.auth_service import AuthService
from app.services.candidate_service import CandidateService
from app.services.election_service import ElectionService
from app.services.house_service import HouseService
from app.services.position_service import PositionService
from app.theme import apply_saved_theme, inject_theme
from app.utils.candidate_image_edit import (
    ZOOM_STEP,
    apply_crop_mode,
    image_to_data_url,
    image_to_png_bytes,
    open_image_bytes,
    rotate_image,
    zoom_image,
)

ELECTION_TYPES = ("Regular", "House")
SORT_OPTIONS = {
    "name_asc": "Name (A-Z)",
    "name_desc": "Name (Z-A)",
    "order_asc": "Display Order",
    "status": "Status",
}
ROLE_CAN_EDIT = {"Administrator", "Super Administrator"}
CLASS_OPTIONS = ["4", "5", "9", "10", "11", "12"]
SECTION_OPTIONS = ["A", "B", "C", "D", "E"]


def _can_edit() -> bool:
    return AuthService.get_user().get("role") in ROLE_CAN_EDIT


def register_candidates_routes() -> None:
    """Register the candidate management page."""

    @ui.page("/candidates")
    @require_auth
    def candidates_page() -> None:
        inject_theme()
        apply_saved_theme()

        state: dict[str, Any] = {
            "election_id": "",
            "election_options": {},
            "election_type": "Regular",
            "candidates": [],
            "positions": [],
            "houses": {},
            "search": "",
            "sort": "name_asc",
            # Pending edited photo for create / before apply upload.
            "pending_photo": None,
            # Working copy inside the image editor dialog.
            "editor_original": None,
            "editor_current": None,
            "editor_filename": "photo.png",
        }

        with admin_shell("/candidates") as content:
            with content:
                with ui.row().classes("items-center justify-between q-mb-lg w-full"):
                    with ui.column().classes("gap-0"):
                        ui.label("Candidates").classes("emp-page-title")
                        ui.label("Add, edit, search, and manage election candidates.").classes("emp-page-subtitle")

                    if _can_edit():
                        ui.button(
                            "Add Candidate",
                            icon="add",
                            on_click=lambda: open_form_dialog(),
                        ).props("unelevated color=primary")

                if not AuthService.has_backend_token():
                    ui.label(
                        "No backend API token in session. Connect to the API with valid credentials "
                        "to manage candidates."
                    ).classes("text-warning text-caption q-mb-md")

                with ui.column().classes("w-full q-mb-md"):
                    ui.label("Election").classes("text-caption text-grey-7")
                    selected_election_label = ui.label("Loading elections…").classes(
                        "text-subtitle1 text-weight-medium q-mb-sm"
                    ).style("color: var(--emp-text);")
                    election_chips = ui.row().classes("w-full flex-wrap q-gutter-sm items-center")

                with ui.row().classes("w-full q-col-gutter-md q-mb-md items-end"):
                    type_tabs = ui.toggle(list(ELECTION_TYPES), value=state["election_type"]).props(
                        "outline toggle-color=primary"
                    ).classes("col-12 col-md-2")
                    search_input = ui.input("Search", placeholder="Search by name").props(
                        "outlined dense clearable"
                    ).classes("col-12 col-md-4")
                    sort_select = ui.select(label="Sort", options=SORT_OPTIONS, value="name_asc").props(
                        "outlined dense"
                    ).classes("col-12 col-md-3")

                list_container = ui.column().classes("w-full q-gutter-sm")
                editing_id: dict[str, str | None] = {"value": None}
                current_image_id: dict[str, str | None] = {"value": None}

                # ── Candidate form dialog ──────────────────────────────────
                with ui.dialog() as dialog, ui.card().classes("q-pa-md").style(
                    "min-width: min(640px, 96vw); max-width: 720px"
                ):
                    form_title = ui.label("Candidate").classes("text-h6 q-mb-md")
                    form_error = ui.label("").classes("text-negative text-caption")
                    form_error.visible = False

                    with ui.row().classes("w-full q-col-gutter-md"):
                        with ui.column().classes("col-12 col-md-7 q-gutter-sm"):
                            form_name = ui.input("Candidate Name").props("outlined dense").classes("w-full")
                            with ui.row().classes("w-full q-col-gutter-sm"):
                                form_class = ui.select(
                                    options=CLASS_OPTIONS,
                                    label="Class",
                                    value="10",
                                ).props("outlined dense").classes("col-6")
                                form_section = ui.select(
                                    options=SECTION_OPTIONS,
                                    label="Section",
                                    value="A",
                                ).props("outlined dense").classes("col-6")
                            form_position = ui.select(options={}, label="Position").props(
                                "outlined dense emit-value map-options"
                            ).classes("w-full")
                            form_house = ui.select(options={}, label="House").props(
                                "outlined dense emit-value map-options"
                            ).classes("w-full")
                            form_house.visible = False
                            form_order = ui.number("Display Order", value=1, min=1, step=1).props(
                                "outlined dense"
                            ).classes("w-full")

                            photo_hint = ui.label(
                                "Open the photo editor to upload, crop, rotate, and preview the ballot card."
                            ).classes("text-caption text-grey-7")
                            with ui.row().classes("items-center q-gutter-sm w-full"):
                                form_thumb = ui.image("").classes("rounded-borders").style(
                                    "width: 56px; height: 56px; object-fit: cover; background: #e5e7eb"
                                )
                                form_thumb.visible = False
                                if _can_edit():
                                    ui.button(
                                        "Open Photo Editor",
                                        icon="photo_camera",
                                        on_click=lambda: ui.timer(0, open_image_editor, once=True),
                                    ).props("outline dense")
                                    ui.upload(
                                        label="Choose Photo",
                                        auto_upload=True,
                                        on_upload=lambda e: ui.timer(
                                            0, lambda: handle_image_upload(e), once=True
                                        ),
                                    ).props("accept=.jpg,.jpeg,.png,.webp,.bmp dense flat").classes("col")

                        with ui.column().classes("col-12 col-md-5 items-center"):
                            ui.label("Ballot Preview").classes("text-caption text-grey-7 q-mb-xs")
                            with ui.column().classes("items-center q-pa-md").style(
                                "width: 200px; min-height: 280px; background: #ffffff; "
                                "border: 1px solid #d1d5db; border-radius: 8px; "
                                "box-shadow: 0 1px 3px rgba(0,0,0,0.08);"
                            ):
                                ballot_photo = (
                                    ui.image("")
                                    .classes("q-mb-sm")
                                    .style(
                                        "width: 140px; height: 140px; object-fit: cover; "
                                        "object-position: center; border-radius: 4px; "
                                        "background: #f3f4f6; display: block; margin: 0 auto;"
                                    )
                                )
                                ballot_photo.visible = False
                                ballot_name = ui.label("Candidate Name").classes(
                                    "text-weight-bold text-center"
                                ).style(
                                    "width: 100%; max-width: 168px; white-space: normal; "
                                    "word-break: break-word; line-height: 1.25; font-size: 14px;"
                                )
                                ballot_meta = ui.label("Class: — - —").classes(
                                    "text-caption text-grey-7 text-center"
                                ).style("width: 100%; max-width: 168px;")
                                ballot_position = ui.label("Position").classes(
                                    "text-caption text-center"
                                ).style("width: 100%; max-width: 168px; color: #6b7280;")

                    with ui.row().classes("justify-end q-gutter-sm q-mt-md w-full"):
                        ui.button("Cancel", on_click=dialog.close).props("flat")
                        if _can_edit():
                            ui.button(
                                "Save",
                                on_click=lambda: ui.timer(0, save_candidate, once=True),
                            ).props("unelevated color=primary")

                # ── Image editor dialog (desktop-style, separate & openable) ─
                with ui.dialog() as editor_dialog, ui.card().classes("q-pa-none").style(
                    "min-width: min(700px, 96vw); max-width: 720px; overflow: hidden;"
                ):
                    with ui.column().classes("w-full items-stretch q-pa-md"):
                        ui.label("IMAGE EDITOR").classes("text-h6 text-weight-bold text-center")
                        ui.label(
                            "Rotate, zoom, and crop — tools sit on the editing canvas."
                        ).classes("text-caption text-primary text-center q-mb-sm")

                        # Dark editing canvas with toolbar INSIDE the frame
                        with ui.element("div").classes("relative-position w-full").style(
                            "background: #111111; border-radius: 8px; "
                            "min-height: 420px; max-height: 520px; overflow: hidden;"
                        ):
                            with ui.column().classes(
                                "w-full items-center justify-center q-pa-md"
                            ).style("min-height: 360px;"):
                                editor_canvas_image = (
                                    ui.image("")
                                    .classes("rounded-borders")
                                    .style(
                                        "max-width: 100%; max-height: 340px; "
                                        "object-fit: contain; display: block; margin: 0 auto;"
                                    )
                                )
                                editor_canvas_image.visible = False
                                editor_empty = ui.label("Upload a photo to begin editing").classes(
                                    "text-grey-5 text-center"
                                )

                            # Toolbar overlay at the bottom of the canvas
                            with ui.element("div").classes("w-full q-pa-sm").style(
                                "background: rgba(17, 17, 17, 0.92); "
                                "border-top: 1px solid rgba(255,255,255,0.12);"
                            ):
                                with ui.row().classes(
                                    "w-full justify-center q-gutter-xs flex-wrap"
                                ):
                                    ui.button(
                                        "Rotate Left",
                                        icon="rotate_left",
                                        on_click=lambda: apply_editor_rotate(-90),
                                    ).props("flat dense color=white")
                                    ui.button(
                                        "Rotate Right",
                                        icon="rotate_right",
                                        on_click=lambda: apply_editor_rotate(90),
                                    ).props("flat dense color=white")
                                    ui.button(
                                        "Zoom +",
                                        icon="zoom_in",
                                        on_click=lambda: apply_editor_zoom(ZOOM_STEP),
                                    ).props("flat dense color=white")
                                    ui.button(
                                        "Zoom -",
                                        icon="zoom_out",
                                        on_click=lambda: apply_editor_zoom(1 / ZOOM_STEP),
                                    ).props("flat dense color=white")
                                    ui.button(
                                        "Portrait",
                                        icon="crop_portrait",
                                        on_click=lambda: apply_editor_crop("portrait"),
                                    ).props("flat dense color=white")
                                    ui.button(
                                        "Square",
                                        icon="crop_square",
                                        on_click=lambda: apply_editor_crop("square"),
                                    ).props("flat dense color=white")
                                    ui.button(
                                        "Landscape",
                                        icon="crop_landscape",
                                        on_click=lambda: apply_editor_crop("landscape"),
                                    ).props("flat dense color=white")
                                    ui.button(
                                        "Reset",
                                        icon="restart_alt",
                                        on_click=lambda: apply_editor_reset(),
                                    ).props("flat dense color=warning")

                        ui.label("Ballot Preview").classes("text-caption text-grey-7 q-mt-md q-mb-xs")
                        with ui.row().classes("w-full justify-center"):
                            with ui.column().classes("items-center q-pa-md").style(
                                "width: 200px; min-height: 260px; background: #ffffff; "
                                "border: 1px solid #d1d5db; border-radius: 8px;"
                            ):
                                editor_ballot_photo = (
                                    ui.image("")
                                    .classes("q-mb-sm")
                                    .style(
                                        "width: 140px; height: 140px; object-fit: cover; "
                                        "object-position: center; border-radius: 4px; "
                                        "background: #f3f4f6; display: block; margin: 0 auto;"
                                    )
                                )
                                editor_ballot_photo.visible = False
                                editor_ballot_name = ui.label("Candidate Name").classes(
                                    "text-weight-bold text-center"
                                ).style(
                                    "width: 100%; max-width: 168px; white-space: normal; "
                                    "word-break: break-word; line-height: 1.25; font-size: 14px;"
                                )
                                editor_ballot_meta = ui.label("Class: — - —").classes(
                                    "text-caption text-grey-7 text-center"
                                ).style("width: 100%; max-width: 168px;")
                                editor_ballot_position = ui.label("Position").classes(
                                    "text-caption text-center"
                                ).style("width: 100%; max-width: 168px; color: #6b7280;")

                        with ui.row().classes("justify-between q-mt-md w-full"):
                            ui.button("Cancel", on_click=lambda: close_image_editor()).props(
                                "unelevated color=negative"
                            )
                            ui.button(
                                "Apply Crop & Save",
                                icon="check",
                                on_click=lambda: ui.timer(0, apply_editor_result, once=True),
                            ).props("unelevated color=positive")

                def _class_section_label() -> str:
                    klass = form_class.value or "—"
                    section = form_section.value or "—"
                    return f"Class: {klass} - {section}"

                def _position_label() -> str:
                    if form_position.value and form_position.options:
                        return str(form_position.options.get(form_position.value, "Position"))
                    return "Position"

                def _house_label() -> str:
                    if form_house.value and form_house.options:
                        return str(form_house.options.get(form_house.value, ""))
                    return ""

                def _sync_house_field_visibility() -> None:
                    is_house = state["election_type"] == "House"
                    form_house.visible = is_house
                    if is_house:
                        form_house.options = state.get("houses") or {}
                        if not form_house.value and form_house.options:
                            form_house.value = next(iter(form_house.options))
                        form_house.update()
                    else:
                        form_house.value = None

                def _update_ballot_labels() -> None:
                    name = (form_name.value or "").strip() or "Candidate Name"
                    meta = _class_section_label()
                    position = _position_label()
                    house = _house_label()
                    if house:
                        position = f"{house} · {position}"
                    ballot_name.text = name
                    ballot_meta.text = meta
                    ballot_position.text = position
                    editor_ballot_name.text = name
                    editor_ballot_meta.text = meta
                    editor_ballot_position.text = position

                def _set_form_preview(data_url: str | None) -> None:
                    if data_url:
                        form_thumb.set_source(data_url)
                        form_thumb.visible = True
                        ballot_photo.set_source(data_url)
                        ballot_photo.visible = True
                    else:
                        form_thumb.visible = False
                        ballot_photo.visible = False

                def _set_editor_canvas(image: Image.Image | None) -> None:
                    if image is None:
                        editor_canvas_image.visible = False
                        editor_ballot_photo.visible = False
                        editor_empty.visible = True
                        return
                    data_url = image_to_data_url(image)
                    editor_canvas_image.set_source(data_url)
                    editor_canvas_image.visible = True
                    editor_ballot_photo.set_source(data_url)
                    editor_ballot_photo.visible = True
                    editor_empty.visible = False

                def _ensure_editor_image() -> Image.Image | None:
                    current = state.get("editor_current")
                    if current is None:
                        ui.notify("Upload a photo first", type="warning")
                        return None
                    return current

                def _filtered_candidates() -> list[dict[str, Any]]:
                    items = [
                        candidate
                        for candidate in state["candidates"]
                        if candidate.get("election_type") == state["election_type"]
                    ]
                    search = state["search"].strip().lower()
                    if search:
                        items = [
                            candidate
                            for candidate in items
                            if search in (candidate.get("candidate_name") or "").lower()
                        ]

                    sort_key = state["sort"]
                    if sort_key == "name_desc":
                        items.sort(key=lambda item: (item.get("candidate_name") or "").lower(), reverse=True)
                    elif sort_key == "order_asc":
                        items.sort(key=lambda item: item.get("display_order", 0))
                    elif sort_key == "status":
                        items.sort(key=lambda item: item.get("status") or "")
                    else:
                        items.sort(key=lambda item: (item.get("candidate_name") or "").lower())
                    return items

                def render_candidates() -> None:
                    list_container.clear()
                    filtered = _filtered_candidates()
                    with list_container:
                        if not filtered:
                            with ui.element("div").classes("emp-placeholder w-full"):
                                ui.icon("groups", size="xl").classes("text-grey-5 q-mb-md")
                                ui.label("No candidates found").classes("text-h6 text-weight-medium")
                                ui.label("Add candidates for the selected election and type.").classes(
                                    "text-caption text-grey-6"
                                )
                            return

                        for candidate in filtered:
                            name = (
                                candidate.get("candidate_name")
                                or candidate.get("name")
                                or "Unnamed candidate"
                            )
                            with ui.card().classes("w-full emp-card"):
                                with ui.row().classes("items-center justify-between w-full"):
                                    with ui.column().classes("gap-0"):
                                        ui.label(name).classes("text-subtitle1 text-weight-medium").style(
                                            "color: var(--emp-text);"
                                        )
                                        class_text = candidate.get("candidate_class") or "—"
                                        section_text = candidate.get("candidate_section") or "—"
                                        ui.label(
                                            f'{candidate.get("position_name", "—")} · '
                                            f'Class {class_text}-{section_text} · '
                                            f'{candidate.get("election_type", "—")}'
                                        ).classes("text-caption").style("color: var(--emp-text-muted);")
                                        if candidate.get("house_name"):
                                            ui.label(candidate["house_name"]).classes("text-caption").style(
                                                "color: var(--emp-text-muted);"
                                            )
                                        photo_status = "Photo ready" if candidate.get("has_image") else "No photo"
                                        ui.label(
                                            f'Status: {candidate.get("status", "—")} · {photo_status}'
                                        ).classes("text-caption").style("color: var(--emp-text-muted);")
                                    with ui.row().classes("q-gutter-sm"):
                                        if _can_edit():
                                            ui.button(
                                                icon="edit",
                                                on_click=lambda c=candidate: open_form_dialog(c),
                                            ).props("flat round")
                                            ui.button(
                                                icon="delete",
                                                color="negative",
                                                on_click=lambda c=candidate: ui.timer(
                                                    0, lambda: delete_candidate(c), once=True
                                                ),
                                            ).props("flat round")

                def render_election_chips() -> None:
                    election_chips.clear()
                    options = state.get("election_options") or {}
                    with election_chips:
                        if not options:
                            ui.label("No elections available").classes("text-caption text-grey-6")
                            return
                        for election_id, election_name in options.items():
                            selected = election_id == state["election_id"]
                            props = "unelevated color=primary dense no-caps" if selected else "outline dense no-caps"

                            def _make_handler(eid: str = election_id, ename: str = election_name):
                                async def _handler() -> None:
                                    await select_election(eid, ename)

                                return _handler

                            ui.button(election_name, on_click=_make_handler()).props(props)

                async def select_election(election_id: str, election_name: str | None = None) -> None:
                    if not election_id:
                        return
                    options = state.get("election_options") or {}
                    name = election_name or options.get(election_id) or election_id
                    state["election_id"] = election_id
                    selected_election_label.set_text(f"Selected: {name}")
                    render_election_chips()
                    await refresh_data()

                async def load_elections() -> None:
                    success, message, elections = await ElectionService.list_elections()
                    if not success:
                        ui.notify(message or "Could not load elections", type="negative")
                        selected_election_label.set_text("Could not load elections")
                        return
                    options = {
                        election["id"]: election.get("name", election.get("election_name", "Election"))
                        for election in elections
                    }
                    state["election_options"] = options
                    if not options:
                        state["election_id"] = ""
                        selected_election_label.set_text("No elections found")
                        render_election_chips()
                        state["candidates"] = []
                        render_candidates()
                        return
                    if state["election_id"] not in options:
                        state["election_id"] = next(iter(options))
                    await select_election(state["election_id"], options[state["election_id"]])
                    await load_houses()

                async def load_houses() -> None:
                    success, message, houses = await HouseService.list_houses()
                    if not success:
                        state["houses"] = {}
                        form_house.options = {}
                        form_house.update()
                        if state["election_type"] == "House":
                            ui.notify(message or "Could not load houses", type="warning")
                        return
                    options = {
                        house["id"]: house.get("house_name") or house.get("name") or house["id"]
                        for house in houses
                    }
                    state["houses"] = options
                    form_house.options = options
                    form_house.update()
                    _sync_house_field_visibility()

                async def refresh_positions() -> None:
                    if not state["election_id"]:
                        state["positions"] = []
                        form_position.options = {}
                        form_position.update()
                        return
                    success, _message, positions = await PositionService.list_positions(
                        election_id=state["election_id"],
                        election_type=state["election_type"],
                    )
                    if success:
                        state["positions"] = positions
                        form_position.options = {
                            position["id"]: position.get("position_name", position.get("name", "Position"))
                            for position in positions
                        }
                    else:
                        state["positions"] = []
                        form_position.options = {}
                    form_position.update()

                async def refresh_candidates() -> None:
                    if not state["election_id"]:
                        state["candidates"] = []
                        render_candidates()
                        return
                    success, message, candidates = await CandidateService.list_candidates(
                        election_id=state["election_id"],
                        election_type=state["election_type"],
                    )
                    if success:
                        state["candidates"] = candidates
                    else:
                        state["candidates"] = []
                        ui.notify(message or "Could not load candidates", type="negative")
                    render_candidates()

                async def refresh_data() -> None:
                    await refresh_positions()
                    await refresh_candidates()

                def open_form_dialog(candidate: dict[str, Any] | None = None) -> None:
                    if not state["election_id"]:
                        ui.notify("Select an election first", type="warning")
                        return

                    form_error.visible = False
                    form_error.text = ""
                    state["pending_photo"] = None
                    state["editor_original"] = None
                    state["editor_current"] = None
                    _set_form_preview(None)
                    _sync_house_field_visibility()

                    if candidate:
                        editing_id["value"] = candidate["id"]
                        form_title.text = "Edit Candidate"
                        form_name.value = candidate.get("candidate_name", "")
                        form_class.value = candidate.get("candidate_class") or "10"
                        form_section.value = candidate.get("candidate_section") or "A"
                        form_position.value = candidate.get("position_id")
                        form_house.value = candidate.get("house_id")
                        form_order.value = candidate.get("display_order", 1)
                        current_image_id["value"] = candidate.get("image_id")
                        photo_hint.text = "Open the photo editor to adjust the candidate photograph."
                        if current_image_id["value"]:
                            ui.timer(0, load_existing_photo_preview, once=True)
                    else:
                        editing_id["value"] = None
                        form_title.text = (
                            "Add House Candidate"
                            if state["election_type"] == "House"
                            else "Add Candidate"
                        )
                        form_name.value = ""
                        form_class.value = "10"
                        form_section.value = "A"
                        form_position.value = next(iter(form_position.options or {}), None)
                        form_house.value = next(iter(form_house.options or {}), None)
                        form_order.value = 1
                        current_image_id["value"] = None
                        photo_hint.text = (
                            "Choose a photo or open the editor — edits work immediately, then Save the candidate."
                        )

                    _update_ballot_labels()
                    dialog.open()

                async def load_existing_photo_preview() -> None:
                    image_id = current_image_id["value"]
                    if not image_id:
                        return
                    success, _message, data_url = await CandidateService.fetch_image_data_url(image_id)
                    if success and data_url:
                        _set_form_preview(data_url)

                async def open_image_editor() -> None:
                    """Open the desktop-style image editor with the current photo loaded."""
                    _update_ballot_labels()
                    state["editor_original"] = None
                    state["editor_current"] = None

                    pending = state.get("pending_photo")
                    if pending and pending.get("content"):
                        try:
                            image = open_image_bytes(pending["content"])
                            state["editor_original"] = image.copy()
                            state["editor_current"] = image.copy()
                            state["editor_filename"] = pending.get("filename") or "photo.png"
                            _set_editor_canvas(image)
                            editor_dialog.open()
                            return
                        except Exception:
                            ui.notify("Could not open queued photo", type="negative")
                            return

                    image_id = current_image_id["value"]
                    if image_id:
                        success, message, raw, _content_type = await CandidateService.fetch_image_bytes(image_id)
                        if not success or not raw:
                            ui.notify(message or "Could not load photo for editing", type="negative")
                            return
                        try:
                            image = open_image_bytes(raw)
                            state["editor_original"] = image.copy()
                            state["editor_current"] = image.copy()
                            state["editor_filename"] = "photo.png"
                            _set_editor_canvas(image)
                            editor_dialog.open()
                            return
                        except Exception:
                            ui.notify("Could not open photo for editing", type="negative")
                            return

                    ui.notify("Choose a photo first using Choose Photo", type="info")

                def close_image_editor() -> None:
                    state["editor_original"] = None
                    state["editor_current"] = None
                    editor_dialog.close()

                def apply_editor_rotate(angle: int) -> None:
                    image = _ensure_editor_image()
                    if image is None:
                        return
                    updated = rotate_image(image, angle)
                    state["editor_current"] = updated
                    _set_editor_canvas(updated)

                def apply_editor_zoom(factor: float) -> None:
                    image = _ensure_editor_image()
                    if image is None:
                        return
                    updated = zoom_image(image, factor)
                    state["editor_current"] = updated
                    _set_editor_canvas(updated)

                def apply_editor_crop(mode: str) -> None:
                    image = _ensure_editor_image()
                    if image is None:
                        return
                    updated = apply_crop_mode(image, mode)
                    state["editor_current"] = updated
                    _set_editor_canvas(updated)
                    ui.notify(f"{mode.title()} crop applied", type="positive")

                def apply_editor_reset() -> None:
                    original = state.get("editor_original")
                    if original is None:
                        ui.notify("Upload a photo first", type="warning")
                        return
                    reset = original.copy()
                    state["editor_current"] = reset
                    _set_editor_canvas(reset)
                    ui.notify("Photo reset to original", type="positive")

                async def apply_editor_result() -> None:
                    image = _ensure_editor_image()
                    if image is None:
                        return

                    png_bytes = image_to_png_bytes(image)
                    filename = state.get("editor_filename") or "photo.png"
                    if not filename.lower().endswith(".png"):
                        filename = f"{filename.rsplit('.', 1)[0]}.png"

                    state["pending_photo"] = {
                        "filename": filename,
                        "content": png_bytes,
                        "content_type": "image/png",
                    }
                    data_url = image_to_data_url(image)
                    _set_form_preview(data_url)
                    photo_hint.text = "Edited photo ready — click Save on the candidate form to keep it."

                    # If the candidate already exists, upload immediately so the server stays in sync.
                    if editing_id["value"]:
                        success, message, data = await CandidateService.upload_image(
                            editing_id["value"],
                            filename=filename,
                            content=png_bytes,
                            content_type="image/png",
                            replace=bool(current_image_id["value"]),
                        )
                        if success and data:
                            current_image_id["value"] = data.get("image_id")
                            state["pending_photo"] = None
                            photo_hint.text = "Photo saved. You can reopen the editor anytime."
                            ui.notify("Photo applied and uploaded", type="positive")
                            await refresh_candidates()
                        else:
                            ui.notify(
                                message or "Photo applied locally — save the candidate to upload",
                                type="warning",
                            )
                    else:
                        ui.notify("Photo applied. Click Save to create the candidate with this photo.", type="info")

                    close_image_editor()

                async def save_candidate() -> None:
                    form_error.visible = False
                    name = (form_name.value or "").strip()
                    if not name:
                        form_error.text = "Candidate name is required."
                        form_error.visible = True
                        return
                    if not form_position.value:
                        form_error.text = "Position is required."
                        form_error.visible = True
                        return
                    if state["election_type"] == "House" and not form_house.value:
                        form_error.text = "House is required for House Election candidates."
                        form_error.visible = True
                        return

                    payload_fields: dict[str, Any] = {
                        "candidate_name": name,
                        "position_id": form_position.value,
                        "candidate_class": form_class.value or None,
                        "candidate_section": form_section.value or None,
                        "display_order": int(form_order.value or 1),
                    }
                    if state["election_type"] == "House":
                        payload_fields["house_id"] = form_house.value

                    if editing_id["value"]:
                        success, message, data = await CandidateService.update_candidate(
                            editing_id["value"],
                            payload_fields,
                        )
                    else:
                        payload = {
                            "election_id": state["election_id"],
                            **payload_fields,
                        }
                        success, message, data = await CandidateService.create_candidate(payload)
                        if success and data:
                            editing_id["value"] = data["id"]

                    if not success:
                        form_error.text = message or "Could not save candidate"
                        form_error.visible = True
                        return

                    pending = state.get("pending_photo")
                    if pending and editing_id["value"]:
                        ok, upload_message, upload_data = await CandidateService.upload_image(
                            editing_id["value"],
                            filename=pending["filename"],
                            content=pending["content"],
                            content_type=pending["content_type"],
                            replace=bool(current_image_id["value"]),
                        )
                        state["pending_photo"] = None
                        if ok and upload_data:
                            current_image_id["value"] = upload_data.get("image_id")
                            await load_existing_photo_preview()
                            photo_hint.text = "Photo uploaded. Reopen the editor to adjust anytime."
                            ui.notify("Candidate and photo saved", type="positive")
                        else:
                            ui.notify(
                                upload_message or "Candidate saved, but photo upload failed",
                                type="warning",
                            )
                    else:
                        ui.notify("Candidate saved", type="positive")

                    form_title.text = "Edit Candidate"
                    await refresh_candidates()
                    _update_ballot_labels()

                async def delete_candidate(candidate: dict[str, Any]) -> None:
                    with ui.dialog() as confirm_dialog, ui.card().classes("q-pa-md"):
                        ui.label("Delete Candidate?").classes("text-h6")
                        ui.label(
                            f'Remove "{candidate.get("candidate_name", "")}"? This cannot be undone.'
                        ).classes("text-body2 q-mt-sm")
                        with ui.row().classes("q-mt-md justify-end q-gutter-sm"):
                            ui.button("Cancel", on_click=confirm_dialog.close).props("flat")
                            ui.button(
                                "Delete",
                                color="negative",
                                on_click=lambda: confirm_dialog.submit("delete"),
                            ).props("unelevated")

                    result = await confirm_dialog
                    if result != "delete":
                        return

                    success, message = await CandidateService.delete_candidate(candidate["id"])
                    if success:
                        ui.notify("Candidate deleted", type="positive")
                        await refresh_candidates()
                    else:
                        ui.notify(message or "Could not delete candidate", type="negative")

                async def handle_image_upload(event: events.UploadEventArguments) -> None:
                    """Load the chosen file into the image editor immediately."""
                    content = await event.file.read()
                    filename = event.file.name or "photo.png"
                    try:
                        image = open_image_bytes(content)
                    except Exception:
                        ui.notify("Unsupported or corrupted image file", type="negative")
                        return

                    state["editor_filename"] = filename
                    state["editor_original"] = image.copy()
                    state["editor_current"] = image.copy()
                    png_name = filename if filename.lower().endswith(".png") else f"{filename.rsplit('.', 1)[0]}.png"
                    state["pending_photo"] = {
                        "filename": png_name,
                        "content": image_to_png_bytes(image),
                        "content_type": "image/png",
                    }
                    _set_form_preview(image_to_data_url(image))
                    _set_editor_canvas(image)
                    _update_ballot_labels()
                    photo_hint.text = "Photo loaded in the editor — adjust, then Apply Crop & Save."
                    editor_dialog.open()

                async def on_filters_change() -> None:
                    state["election_type"] = type_tabs.value or "Regular"
                    state["search"] = search_input.value or ""
                    state["sort"] = sort_select.value or "name_asc"
                    _sync_house_field_visibility()
                    await refresh_data()

                form_name.on("update:model-value", lambda: _update_ballot_labels())
                form_class.on("update:model-value", lambda: _update_ballot_labels())
                form_section.on("update:model-value", lambda: _update_ballot_labels())
                form_position.on("update:model-value", lambda: _update_ballot_labels())
                form_house.on("update:model-value", lambda: _update_ballot_labels())
                type_tabs.on_value_change(lambda _e: ui.timer(0, on_filters_change, once=True))
                search_input.on(
                    "update:model-value",
                    lambda: (state.update({"search": search_input.value or ""}), render_candidates()),
                )
                sort_select.on(
                    "update:model-value",
                    lambda: (state.update({"sort": sort_select.value or "name_asc"}), render_candidates()),
                )

                ui.timer(0.1, load_elections, once=True)
