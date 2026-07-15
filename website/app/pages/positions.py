"""Position management page."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.services.auth_service import AuthService
from app.services.position_service import PositionService
from app.theme import apply_saved_theme, inject_theme

ELECTION_TYPES = ("Regular", "House")
ROLE_CAN_EDIT = {"Administrator", "Super Administrator"}


def _can_edit() -> bool:
    return AuthService.get_user().get("role") in ROLE_CAN_EDIT


def register_positions_routes() -> None:
    """Register the position management page."""

    @ui.page("/positions")
    @require_auth
    def positions_page() -> None:
        inject_theme()
        apply_saved_theme()

        state: dict[str, Any] = {
            "election_id": "",
            "election_options": {},
            "positions": [],
            "selected_type": "Regular",
            "search": "",
            "status_filter": "all",
        }

        with admin_shell("/positions") as content:
            with content:
                with ui.row().classes("items-center justify-between q-mb-lg w-full"):
                    with ui.column().classes("gap-0"):
                        ui.label("Positions").classes("emp-page-title")
                        ui.label("Create, organize, and manage election positions.").classes("emp-page-subtitle")
                    if _can_edit():
                        ui.button(
                            "Add Position",
                            icon="add",
                            on_click=lambda: open_create_dialog(),
                        ).props("unelevated color=primary")

                if not AuthService.has_backend_token():
                    ui.label(
                        "No backend API token in session. Connect to the API with valid credentials "
                        "to load and save positions."
                    ).classes("text-warning text-caption q-mb-md")

                with ui.row().classes("w-full q-col-gutter-md q-mb-sm items-end"):
                    election_select = ui.select(
                        label="Election",
                        options={},
                        with_input=True,
                    ).props("outlined dense emit-value map-options").classes("col-12 col-md-4")

                    type_tabs = ui.toggle(list(ELECTION_TYPES), value=state["selected_type"]).props(
                        "outline toggle-color=primary"
                    ).classes("col-12 col-md-3")

                    search_input = ui.input("Search positions", placeholder="Search by name").props(
                        "outlined dense clearable"
                    ).classes("col-12 col-md-3")

                    status_filter = ui.select(
                        label="Status",
                        options={"all": "All", "active": "Active", "inactive": "Inactive"},
                        value="all",
                    ).props("outlined dense").classes("col-12 col-md-2")

                ui.label(
                    "Regular and House run separately: switch the toggle to manage each list. "
                    "Ballot order (1, 2, 3…) is counted only within the selected type."
                ).classes("text-caption text-grey-7 q-mb-md")

                list_container = ui.column().classes("w-full q-gutter-sm")
                editing_id: dict[str, str | None] = {"value": None}

                with ui.dialog() as dialog, ui.card().classes("q-pa-md").style("min-width: 420px"):
                    form_title = ui.label("Add Position").classes("text-h6 q-mb-md")
                    form_error = ui.label("").classes("text-negative text-caption")
                    form_error.visible = False
                    form_name = ui.input("Position Name").props("outlined dense").classes("w-full")
                    form_type_label = ui.label("").classes("text-body2 text-grey-8 q-mb-sm")
                    form_winners = ui.number("Number of Winners", value=1, min=1, step=1).props(
                        "outlined dense"
                    ).classes("w-full")
                    form_order = ui.number(
                        "Ballot order (within this type)",
                        value=1,
                        min=1,
                        step=1,
                    ).props("outlined dense").classes("w-full")
                    ui.label(
                        "Leave as suggested to append at the end of this Regular or House list."
                    ).classes("text-caption text-grey-6")
                    with ui.row().classes("q-mt-md justify-end q-gutter-sm"):
                        ui.button("Cancel", on_click=dialog.close).props("flat")
                        ui.button(
                            "Save",
                            color="primary",
                            on_click=lambda: ui.timer(0, save_position, once=True),
                        ).props("unelevated")

                def _filtered_positions() -> list[dict[str, Any]]:
                    # Positions are already loaded for the selected election type.
                    items = list(state["positions"])
                    if state["status_filter"] == "active":
                        items = [position for position in items if position.get("active")]
                    elif state["status_filter"] == "inactive":
                        items = [position for position in items if not position.get("active")]

                    search = state["search"].strip().lower()
                    if search:
                        items = [
                            position
                            for position in items
                            if search in (position.get("position_name") or position.get("name") or "").lower()
                        ]
                    return sorted(items, key=lambda item: item.get("display_order", 0))

                def _next_order_for_type() -> int:
                    orders = [int(item.get("display_order") or 0) for item in state["positions"]]
                    return (max(orders) if orders else 0) + 1

                def _apply_election_options(options: dict[str, str]) -> None:
                    state["election_options"] = options
                    election_select.options = options
                    if options:
                        if state["election_id"] not in options:
                            state["election_id"] = next(iter(options))
                        election_select.value = state["election_id"]
                    else:
                        state["election_id"] = ""
                        election_select.value = None
                    election_select.update()

                async def load_elections() -> None:
                    success, message, elections = await PositionService.list_elections()
                    if not success:
                        ui.notify(message or "Could not load elections", type="warning")
                        _apply_election_options({})
                        render_positions()
                        return

                    options = {
                        item["id"]: item.get("name") or item.get("election_name") or item["id"]
                        for item in elections
                    }
                    _apply_election_options(options)
                    if not options:
                        ui.notify(
                            "No elections yet. Create one under Election Management first.",
                            type="warning",
                        )
                    await refresh_positions()

                async def refresh_positions() -> None:
                    if not state["election_id"]:
                        state["positions"] = []
                        render_positions()
                        return

                    success, message, positions = await PositionService.list_positions(
                        election_id=state["election_id"],
                        election_type=state["selected_type"],
                    )
                    if success:
                        state["positions"] = positions
                        render_positions()
                    else:
                        ui.notify(message or "Could not load positions", type="negative")
                        state["positions"] = []
                        render_positions()

                def render_positions() -> None:
                    list_container.clear()
                    items = _filtered_positions()

                    with list_container:
                        if not state["election_options"]:
                            with ui.element("div").classes("emp-placeholder w-full"):
                                ui.icon("ballot", size="xl").classes("text-grey-5 q-mb-md")
                                ui.label("No elections available").classes("text-h6 text-weight-medium")
                                ui.label(
                                    "Create an election in Election Management, then return here to add positions."
                                ).classes("text-body2 text-grey-6 q-mt-sm")
                            return

                        if not state["election_id"]:
                            with ui.element("div").classes("emp-placeholder w-full"):
                                ui.icon("how_to_vote", size="xl").classes("text-grey-5 q-mb-md")
                                ui.label("Select an election").classes("text-h6 text-weight-medium")
                                ui.label("Choose an election above to manage its positions.").classes(
                                    "text-body2 text-grey-6 q-mt-sm"
                                )
                            return

                        if not items:
                            with ui.element("div").classes("emp-placeholder w-full"):
                                ui.icon("badge", size="xl").classes("text-grey-5 q-mb-md")
                                ui.label(f"No {state['selected_type'].lower()} positions yet").classes(
                                    "text-h6 text-weight-medium"
                                )
                                ui.label(
                                    f"Add Position will create the next {state['selected_type']} role "
                                    "with its own ballot order (1, 2, 3…)."
                                ).classes("text-body2 text-grey-6 q-mt-sm")
                            return

                        for position in items:
                            with ui.element("div").classes("emp-card q-pa-md w-full"):
                                with ui.row().classes("items-center justify-between w-full"):
                                    with ui.row().classes("items-center q-gutter-md"):
                                        ui.badge(str(position.get("display_order", 0)), color="primary").props(
                                            "outline"
                                        )
                                        with ui.column().classes("gap-0"):
                                            ui.label(
                                                position.get("position_name") or position.get("name") or ""
                                            ).classes("text-weight-medium")
                                            ui.label(
                                                f"Winners: {position.get('winner_count', 1)} · "
                                                f"Candidates: {position.get('candidate_count', 0)}"
                                            ).classes("text-caption text-grey-7")
                                    with ui.row().classes("items-center q-gutter-sm"):
                                        status_color = "positive" if position.get("active") else "grey"
                                        ui.badge(
                                            "Active" if position.get("active") else "Inactive",
                                            color=status_color,
                                        ).props("outline")

                                        if _can_edit():
                                            ui.button(
                                                icon="arrow_upward",
                                                on_click=lambda p=position: ui.timer(
                                                    0, lambda: move_up(p), once=True
                                                ),
                                            ).props("flat round dense")
                                            ui.button(
                                                icon="arrow_downward",
                                                on_click=lambda p=position: ui.timer(
                                                    0, lambda: move_down(p), once=True
                                                ),
                                            ).props("flat round dense")
                                            ui.button(
                                                icon="edit",
                                                on_click=lambda p=position: open_edit_dialog(p),
                                            ).props("flat round dense color=primary")
                                            ui.button(
                                                icon="pause" if position.get("active") else "play_arrow",
                                                on_click=lambda p=position: ui.timer(
                                                    0, lambda: toggle_status(p), once=True
                                                ),
                                            ).props("flat round dense color=warning")
                                            ui.button(
                                                icon="delete",
                                                on_click=lambda p=position: ui.timer(
                                                    0, lambda: delete_position(p), once=True
                                                ),
                                            ).props("flat round dense color=negative")

                async def move_up(position: dict[str, Any]) -> None:
                    success, message, _ = await PositionService.move_position(position["id"], "up")
                    if success:
                        await refresh_positions()
                    else:
                        ui.notify(message or "Could not move position", type="negative")

                async def move_down(position: dict[str, Any]) -> None:
                    success, message, _ = await PositionService.move_position(position["id"], "down")
                    if success:
                        await refresh_positions()
                    else:
                        ui.notify(message or "Could not move position", type="negative")

                async def toggle_status(position: dict[str, Any]) -> None:
                    if position.get("active"):
                        success, message, _ = await PositionService.disable_position(position["id"])
                    else:
                        success, message, _ = await PositionService.enable_position(position["id"])
                    if success:
                        await refresh_positions()
                    else:
                        ui.notify(message or "Could not update position status", type="negative")

                async def delete_position(position: dict[str, Any]) -> None:
                    with ui.dialog() as confirm_dialog, ui.card().classes("q-pa-md"):
                        ui.label("Delete Position?").classes("text-h6")
                        ui.label(
                            f'Remove "{position.get("position_name") or position.get("name") or ""}"? '
                            "This cannot be undone."
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

                    success, message = await PositionService.delete_position(position["id"])
                    if success:
                        ui.notify("Position deleted", type="positive")
                        await refresh_positions()
                    else:
                        ui.notify(message or "Could not delete position", type="negative")

                def open_create_dialog() -> None:
                    if not state["election_id"]:
                        ui.notify("Select an election first", type="warning")
                        return
                    editing_id["value"] = None
                    form_title.text = f"Add {state['selected_type']} Position"
                    form_error.visible = False
                    form_error.text = ""
                    form_name.value = ""
                    form_type_label.text = (
                        f"Election type: {state['selected_type']} "
                        "(from the Regular / House toggle — order is separate for each)"
                    )
                    form_winners.value = 1
                    form_order.value = _next_order_for_type()
                    dialog.open()

                def open_edit_dialog(position: dict[str, Any]) -> None:
                    editing_id["value"] = position["id"]
                    position_type = position.get("election_type") or state["selected_type"]
                    form_title.text = f"Edit {position_type} Position"
                    form_error.visible = False
                    form_error.text = ""
                    form_name.value = position.get("position_name") or position.get("name") or ""
                    form_type_label.text = (
                        f"Election type: {position_type} (ballot order is within this type only)"
                    )
                    form_winners.value = position.get("winner_count", 1)
                    form_order.value = position.get("display_order", 1)
                    dialog.open()

                async def save_position() -> None:
                    form_error.visible = False
                    name = (form_name.value or "").strip()
                    if not name:
                        form_error.text = "Position name is required."
                        form_error.visible = True
                        return

                    if editing_id["value"]:
                        payload = {
                            "name": name,
                            "winner_count": int(form_winners.value or 1),
                            "display_order": int(form_order.value or 1),
                        }
                        success, message, _ = await PositionService.update_position(editing_id["value"], payload)
                    else:
                        # Omit display_order when using the suggested next value so the API
                        # assigns max+1 within this election type only.
                        suggested = _next_order_for_type()
                        chosen = int(form_order.value or suggested)
                        payload: dict[str, Any] = {
                            "election_id": state["election_id"],
                            "name": name,
                            "election_type": state["selected_type"],
                            "winner_count": int(form_winners.value or 1),
                        }
                        if chosen != suggested:
                            payload["display_order"] = chosen
                        success, message, _ = await PositionService.create_position(payload)

                    if success:
                        dialog.close()
                        ui.notify("Position saved", type="positive")
                        await refresh_positions()
                    else:
                        form_error.text = message or "Could not save position"
                        form_error.visible = True

                async def on_election_change() -> None:
                    state["election_id"] = election_select.value or ""
                    await refresh_positions()

                async def on_filters_change() -> None:
                    previous_type = state["selected_type"]
                    state["selected_type"] = type_tabs.value or "Regular"
                    state["search"] = search_input.value or ""
                    state["status_filter"] = status_filter.value or "all"
                    if state["selected_type"] != previous_type:
                        await refresh_positions()
                    else:
                        render_positions()

                election_select.on("update:model-value", lambda: ui.timer(0, on_election_change, once=True))
                type_tabs.on("update:model-value", lambda: ui.timer(0, on_filters_change, once=True))
                search_input.on("update:model-value", lambda: ui.timer(0, on_filters_change, once=True))
                status_filter.on("update:model-value", lambda: ui.timer(0, on_filters_change, once=True))

                render_positions()
                ui.timer(0.1, load_elections, once=True)
