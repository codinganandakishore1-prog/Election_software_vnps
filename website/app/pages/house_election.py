"""House election management page."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.services.auth_service import AuthService
from app.services.house_service import HouseService
from app.theme import apply_saved_theme, inject_theme

ROLE_CAN_EDIT = {"Administrator", "Super Administrator"}
HOUSE_TAB = "Houses"
POSITIONS_TAB = "Positions"
CANDIDATES_TAB = "Candidates"
NODES_TAB = "Node Assignment"
VALIDATION_TAB = "Validation"
TABS = (HOUSE_TAB, POSITIONS_TAB, CANDIDATES_TAB, NODES_TAB, VALIDATION_TAB)


def _can_edit() -> bool:
    return AuthService.get_user().get("role") in ROLE_CAN_EDIT


def register_house_election_routes() -> None:
    """Register the house election management page."""

    @ui.page("/house-election")
    @require_auth
    def house_election_page() -> None:
        inject_theme()
        apply_saved_theme()

        state: dict[str, Any] = {
            "election_id": "",
            "houses": [],
            "configuration": None,
            "candidates": [],
            "nodes": [],
            "selected_house_id": "",
            "validation": None,
        }

        with admin_shell("/house-election") as content:
            with content:
                with ui.row().classes("items-center justify-between q-mb-lg w-full"):
                    with ui.column().classes("gap-0"):
                        ui.label("House Election").classes("emp-page-title")
                        ui.label(
                            "Manage Pallava, Pandya, Chera, and Chola house elections."
                        ).classes("emp-page-subtitle")

                if not AuthService.has_backend_token():
                    ui.label(
                        "No backend API token in session. Connect to the API with valid credentials "
                        "to load and save house configuration."
                    ).classes("text-warning text-caption q-mb-md")

                with ui.row().classes("w-full q-col-gutter-md q-mb-md items-end"):
                    election_select = ui.select(
                        label="Election",
                        options={},
                        with_input=True,
                    ).props("outlined dense emit-value map-options").classes("col-12 col-md-4")

                tabs = ui.tabs().classes("w-full")
                with tabs:
                    for tab_name in TABS:
                        ui.tab(tab_name)

                with ui.tab_panels(tabs, value=HOUSE_TAB).classes("w-full q-mt-md"):
                    with ui.tab_panel(HOUSE_TAB):
                        houses_panel = ui.column().classes("w-full q-gutter-md")
                    with ui.tab_panel(POSITIONS_TAB):
                        positions_panel = ui.column().classes("w-full q-gutter-md")
                    with ui.tab_panel(CANDIDATES_TAB):
                        candidates_panel = ui.column().classes("w-full q-gutter-md")
                    with ui.tab_panel(NODES_TAB):
                        nodes_panel = ui.column().classes("w-full q-gutter-md")
                    with ui.tab_panel(VALIDATION_TAB):
                        validation_panel = ui.column().classes("w-full q-gutter-md")

                # Empty placeholders until the first load completes
                with houses_panel:
                    ui.label("Loading houses…").classes("text-caption text-grey-6")
                with positions_panel:
                    ui.label("Select an election to view house positions.").classes("text-caption text-grey-6")
                with candidates_panel:
                    ui.label("Select an election to manage house candidates.").classes("text-caption text-grey-6")
                with nodes_panel:
                    ui.label("Loading nodes…").classes("text-caption text-grey-6")
                with validation_panel:
                    ui.label("Select an election, then run validation.").classes("text-caption text-grey-6")

                candidate_dialog = ui.dialog()
                candidate_error = ui.label("").classes("text-negative text-caption")
                candidate_error.visible = False
                candidate_name_input = ui.input("Candidate Name").props("outlined dense").classes("w-full")
                candidate_class_select = ui.select(
                    options=["4", "5", "9", "10", "11", "12"],
                    label="Class",
                    value="10",
                ).props("outlined dense").classes("w-full")
                candidate_section_select = ui.select(
                    options=["A", "B", "C", "D", "E"],
                    label="Section",
                    value="A",
                ).props("outlined dense").classes("w-full")
                candidate_position_select = ui.select(options={}, label="Position").props(
                    "outlined dense emit-value map-options"
                ).classes("w-full")
                candidate_house_select = ui.select(options={}, label="House").props(
                    "outlined dense emit-value map-options"
                ).classes("w-full")
                candidate_order_input = ui.number("Display Order", value=1, min=1, step=1).props(
                    "outlined dense"
                ).classes("w-full")
                editing_candidate_id: dict[str, str | None] = {"value": None}

                node_dialog = ui.dialog()
                node_error = ui.label("").classes("text-negative text-caption")
                node_error.visible = False
                node_name_input = ui.input("Node Name").props("outlined dense").classes("w-full")
                node_type_select = ui.select(
                    options=["Regular", "House"],
                    label="Election Type",
                ).props("outlined dense").classes("w-full")
                node_house_select = ui.select(options={}, label="Assigned House").props(
                    "outlined dense emit-value map-options"
                ).classes("w-full")
                editing_node_id: dict[str, str | None] = {"value": None}

                async def load_elections() -> None:
                    success, message, elections = await HouseService.list_elections()
                    if not success:
                        ui.notify(message or "Could not load elections", type="warning")
                        render_houses()
                        return

                    options = {
                        item["id"]: item.get("election_name") or item.get("name") or item["id"]
                        for item in elections
                    }
                    election_select.options = options
                    if options and not state["election_id"]:
                        state["election_id"] = next(iter(options))
                        election_select.value = state["election_id"]
                    elif not options:
                        election_select.value = None
                        state["election_id"] = ""
                    election_select.update()
                    await refresh_all()

                async def refresh_houses() -> None:
                    success, message, houses = await HouseService.list_houses()
                    if success:
                        state["houses"] = houses
                        house_options = {house["id"]: house["house_name"] for house in houses}
                        candidate_house_select.options = house_options
                        node_house_select.options = house_options
                        if house_options and not state["selected_house_id"]:
                            state["selected_house_id"] = next(iter(house_options))
                        candidate_house_select.update()
                        node_house_select.update()
                    else:
                        ui.notify(message or "Could not load houses", type="negative")
                    render_houses()

                async def refresh_configuration() -> None:
                    if not state["election_id"]:
                        state["configuration"] = None
                        render_positions()
                        return

                    success, message, configuration = await HouseService.get_configuration(state["election_id"])
                    if success:
                        state["configuration"] = configuration
                    else:
                        state["configuration"] = None
                        ui.notify(message or "Could not load house configuration", type="negative")
                    render_positions()

                async def refresh_candidates() -> None:
                    if not state["election_id"]:
                        state["candidates"] = []
                        render_candidates()
                        return

                    success, message, candidates = await HouseService.list_candidates(state["election_id"])
                    if success:
                        state["candidates"] = candidates
                    else:
                        state["candidates"] = []
                        ui.notify(message or "Could not load house candidates", type="negative")
                    render_candidates()

                async def refresh_nodes() -> None:
                    success, message, nodes = await HouseService.list_nodes()
                    if success:
                        state["nodes"] = nodes
                    else:
                        state["nodes"] = []
                        ui.notify(message or "Could not load nodes", type="negative")
                    render_nodes()

                async def refresh_all() -> None:
                    await refresh_houses()
                    await refresh_configuration()
                    await refresh_candidates()
                    await refresh_nodes()

                def render_houses() -> None:
                    houses_panel.clear()
                    with houses_panel:
                        if not state["houses"]:
                            with ui.element("div").classes("emp-placeholder w-full"):
                                ui.icon("home", size="xl").classes("text-grey-5 q-mb-md")
                                ui.label("No houses configured").classes("text-h6 text-weight-medium")
                                ui.label(
                                    "Default houses (Pallava, Pandya, Chera, Chola) should appear after the database is seeded."
                                ).classes("text-caption text-grey-6")
                            return

                        with ui.row().classes("w-full q-col-gutter-md"):
                            for house in state["houses"]:
                                with ui.element("div").classes("emp-card q-pa-md col-12 col-sm-6 col-md-3"):
                                    color = house.get("color") or "#607D8B"
                                    ui.icon("home", size="lg").style(f"color: {color}")
                                    ui.label(house.get("house_name", "")).classes("text-h6 text-weight-medium q-mt-sm")
                                    ui.label("Active" if house.get("active") else "Inactive").classes(
                                        "text-caption text-grey-7"
                                    )

                def render_positions() -> None:
                    positions_panel.clear()
                    configuration = state.get("configuration") or {}
                    positions = configuration.get("positions") or []

                    with positions_panel:
                        ui.label(
                            "House positions apply to all four houses. Manage them on the Positions page."
                        ).classes("text-body2 text-grey-7 q-mb-sm")

                        if not positions:
                            with ui.element("div").classes("emp-placeholder w-full"):
                                ui.icon("badge", size="xl").classes("text-grey-5 q-mb-md")
                                ui.label("No house positions yet").classes("text-h6 text-weight-medium")
                                ui.label(
                                    "Add House-type positions on the Positions page."
                                ).classes("text-body2 text-grey-6 q-mt-sm")
                            return

                        for position in positions:
                            with ui.element("div").classes("emp-card q-pa-md w-full"):
                                with ui.row().classes("items-center justify-between w-full"):
                                    with ui.column().classes("gap-0"):
                                        ui.label(
                                            f'{position.get("display_order", 0)}. {position.get("position_name", "")}'
                                        ).classes("text-weight-medium")
                                        coverage = position.get("candidate_count_by_house") or {}
                                        covered = sum(1 for count in coverage.values() if count > 0)
                                        ui.label(
                                            f"Candidates across houses: {covered}/4"
                                        ).classes("text-caption text-grey-7")

                def render_candidates() -> None:
                    candidates_panel.clear()
                    configuration = state.get("configuration") or {}
                    position_options = {
                        position["id"]: position["position_name"]
                        for position in configuration.get("positions") or []
                    }
                    candidate_position_select.options = position_options
                    candidate_position_select.update()

                    filtered = state["candidates"]
                    if state["selected_house_id"]:
                        filtered = [
                            candidate
                            for candidate in state["candidates"]
                            if candidate.get("house_id") == state["selected_house_id"]
                        ]

                    with candidates_panel:
                        with ui.row().classes("w-full q-col-gutter-md items-end q-mb-md"):
                            house_filter = ui.select(
                                label="Filter by House",
                                options={"": "All Houses", **{
                                    house["id"]: house["house_name"] for house in state["houses"]
                                }},
                                value=state["selected_house_id"],
                            ).props("outlined dense").classes("col-12 col-md-4")

                            if _can_edit():
                                ui.button(
                                    "Add Candidate",
                                    icon="person_add",
                                    color="primary",
                                    on_click=open_create_candidate_dialog,
                                ).props("unelevated").classes("col-auto")

                            async def on_house_filter_change() -> None:
                                state["selected_house_id"] = house_filter.value or ""
                                render_candidates()

                            house_filter.on(
                                "update:model-value",
                                lambda: ui.timer(0, on_house_filter_change, once=True),
                            )

                        if not filtered:
                            with ui.element("div").classes("emp-placeholder w-full"):
                                ui.icon("groups", size="xl").classes("text-grey-5 q-mb-md")
                                ui.label("No house candidates found").classes("text-h6 text-weight-medium")
                            return

                        for candidate in filtered:
                            with ui.element("div").classes("emp-card q-pa-md w-full"):
                                with ui.row().classes("items-center justify-between w-full"):
                                    with ui.column().classes("gap-0"):
                                        ui.label(candidate.get("candidate_name", "")).classes("text-weight-medium")
                                        class_text = candidate.get("candidate_class") or "—"
                                        section_text = candidate.get("candidate_section") or "—"
                                        ui.label(
                                            f'{candidate.get("house_name", "")} · '
                                            f'{candidate.get("position_name", "")} · '
                                            f'Class {class_text}-{section_text} · '
                                            f'Order {candidate.get("display_order", 1)}'
                                        ).classes("text-caption text-grey-7")
                                    with ui.row().classes("items-center q-gutter-sm"):
                                        photo_color = "positive" if candidate.get("has_image") else "warning"
                                        ui.badge(
                                            "Photo" if candidate.get("has_image") else "No Photo",
                                            color=photo_color,
                                        ).props("outline")
                                        if _can_edit():
                                            ui.button(
                                                icon="edit",
                                                on_click=lambda c=candidate: open_edit_candidate_dialog(c),
                                            ).props("flat round dense color=primary")
                                            ui.button(
                                                icon="delete",
                                                on_click=lambda c=candidate: ui.timer(
                                                    0, lambda: delete_candidate(c), once=True
                                                ),
                                            ).props("flat round dense color=negative")

                def render_nodes() -> None:
                    nodes_panel.clear()
                    house_nodes = [node for node in state["nodes"] if node.get("election_type") == "House"]
                    regular_nodes = [node for node in state["nodes"] if node.get("election_type") == "Regular"]

                    with nodes_panel:
                        ui.label(
                            "House assignment is configured here. Teachers and students never choose the house."
                        ).classes("text-body2 text-grey-7 q-mb-md")

                        if house_nodes:
                            ui.label("House Nodes").classes("text-subtitle1 text-weight-medium q-mb-sm")
                            for node in house_nodes:
                                _render_node_card(node)
                        else:
                            ui.label("No house nodes registered.").classes("text-caption text-grey-6 q-mb-md")

                        if regular_nodes:
                            ui.label("Regular Nodes").classes("text-subtitle1 text-weight-medium q-mt-md q-mb-sm")
                            for node in regular_nodes:
                                _render_node_card(node)

                def _render_node_card(node: dict[str, Any]) -> None:
                    with ui.element("div").classes("emp-card q-pa-md w-full q-mb-sm"):
                        with ui.row().classes("items-center justify-between w-full"):
                            with ui.column().classes("gap-0"):
                                ui.label(node.get("node_name", "")).classes("text-weight-medium")
                                house_label = node.get("house_name") or "No house assigned"
                                ui.label(
                                    f'{node.get("election_type", "")} · {house_label}'
                                ).classes("text-caption text-grey-7")
                            if _can_edit():
                                ui.button(
                                    icon="edit",
                                    on_click=lambda n=node: open_edit_node_dialog(n),
                                ).props("flat round dense color=primary")

                def render_validation() -> None:
                    validation_panel.clear()
                    result = state.get("validation")

                    with validation_panel:
                        ui.button(
                            "Run Validation",
                            icon="fact_check",
                            color="primary",
                            on_click=lambda: ui.timer(0, run_validation, once=True),
                        ).props("unelevated").classes("self-start q-mb-md")

                        if result is None:
                            ui.label(
                                "Validate house configuration, candidates, and node assignments before publishing."
                            ).classes("text-body2 text-grey-7")
                            return

                        if result.get("valid"):
                            ui.label("House configuration is valid.").classes("text-positive text-weight-medium")
                        else:
                            ui.label("Validation failed.").classes("text-negative text-weight-medium q-mb-sm")
                            for error in result.get("errors") or []:
                                ui.label(f"• {error}").classes("text-body2 text-negative")

                def open_create_candidate_dialog() -> None:
                    if not state["election_id"]:
                        ui.notify("Select an election first", type="warning")
                        return
                    if not (state.get("configuration") or {}).get("positions"):
                        ui.notify("Add House positions on the Positions page first", type="warning")
                        return
                    editing_candidate_id["value"] = None
                    candidate_error.visible = False
                    candidate_name_input.value = ""
                    candidate_class_select.value = "10"
                    candidate_section_select.value = "A"
                    candidate_position_select.value = next(iter(candidate_position_select.options or {}), None)
                    candidate_house_select.value = state["selected_house_id"] or next(
                        iter(candidate_house_select.options or {}),
                        None,
                    )
                    candidate_order_input.value = 1
                    candidate_dialog.open()

                def open_edit_candidate_dialog(candidate: dict[str, Any]) -> None:
                    editing_candidate_id["value"] = candidate["id"]
                    candidate_error.visible = False
                    candidate_name_input.value = candidate.get("candidate_name", "")
                    candidate_class_select.value = candidate.get("candidate_class") or "10"
                    candidate_section_select.value = candidate.get("candidate_section") or "A"
                    candidate_position_select.value = candidate.get("position_id")
                    candidate_house_select.value = candidate.get("house_id")
                    candidate_order_input.value = candidate.get("display_order", 1)
                    candidate_dialog.open()

                async def save_candidate() -> None:
                    candidate_error.visible = False
                    name = (candidate_name_input.value or "").strip()
                    if not name:
                        candidate_error.text = "Candidate name is required."
                        candidate_error.visible = True
                        return
                    if not candidate_position_select.value:
                        candidate_error.text = "Position is required."
                        candidate_error.visible = True
                        return
                    if not candidate_house_select.value:
                        candidate_error.text = "House is required for House Election candidates."
                        candidate_error.visible = True
                        return

                    payload = {
                        "election_id": state["election_id"],
                        "candidate_name": name,
                        "position_id": candidate_position_select.value,
                        "house_id": candidate_house_select.value,
                        "candidate_class": candidate_class_select.value or None,
                        "candidate_section": candidate_section_select.value or None,
                        "display_order": int(candidate_order_input.value or 1),
                    }

                    if editing_candidate_id["value"]:
                        success, message, _ = await HouseService.update_candidate(
                            editing_candidate_id["value"],
                            payload,
                        )
                    else:
                        success, message, _ = await HouseService.create_candidate(payload)

                    if success:
                        candidate_dialog.close()
                        ui.notify("Candidate saved", type="positive")
                        await refresh_candidates()
                        await refresh_configuration()
                    else:
                        candidate_error.text = message or "Could not save candidate"
                        candidate_error.visible = True

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

                    success, message = await HouseService.delete_candidate(candidate["id"])
                    if success:
                        ui.notify("Candidate deleted", type="positive")
                        await refresh_candidates()
                        await refresh_configuration()
                    else:
                        ui.notify(message or "Could not delete candidate", type="negative")

                def open_edit_node_dialog(node: dict[str, Any]) -> None:
                    editing_node_id["value"] = node["id"]
                    node_error.visible = False
                    node_name_input.value = node.get("node_name", "")
                    node_type_select.value = node.get("election_type", "House")
                    node_house_select.value = node.get("house_id")
                    node_dialog.open()

                async def save_node() -> None:
                    node_error.visible = False
                    if not editing_node_id["value"]:
                        return

                    payload: dict[str, Any] = {
                        "node_name": (node_name_input.value or "").strip(),
                        "election_type": node_type_select.value,
                    }
                    if node_type_select.value == "House":
                        payload["house_id"] = node_house_select.value
                    else:
                        payload["house_id"] = None

                    success, message, _ = await HouseService.update_node(editing_node_id["value"], payload)
                    if success:
                        node_dialog.close()
                        ui.notify("Node assignment saved", type="positive")
                        await refresh_nodes()
                    else:
                        node_error.text = message or "Could not save node assignment"
                        node_error.visible = True

                async def run_validation() -> None:
                    if not state["election_id"]:
                        ui.notify("Select an election first", type="warning")
                        return
                    success, message, result = await HouseService.validate(state["election_id"])
                    if success:
                        state["validation"] = result
                        render_validation()
                    else:
                        ui.notify(message or "Validation failed", type="negative")

                with candidate_dialog, ui.card().classes("q-pa-md").style("min-width: 420px") as house_candidate_card:
                    ui.label("House Candidate").classes("text-h6 q-mb-md")
                    candidate_name_input.move(house_candidate_card)
                    candidate_class_select.move(house_candidate_card)
                    candidate_section_select.move(house_candidate_card)
                    candidate_position_select.move(house_candidate_card)
                    candidate_house_select.move(house_candidate_card)
                    candidate_order_input.move(house_candidate_card)
                    candidate_error.move(house_candidate_card)
                    with ui.row().classes("q-mt-md justify-end q-gutter-sm"):
                        ui.button("Cancel", on_click=candidate_dialog.close).props("flat")
                        ui.button(
                            "Save",
                            color="primary",
                            on_click=lambda: ui.timer(0, save_candidate, once=True),
                        ).props("unelevated")

                with node_dialog, ui.card().classes("q-pa-md").style("min-width: 420px") as house_node_card:
                    ui.label("Node Assignment").classes("text-h6 q-mb-md")
                    node_name_input.move(house_node_card)
                    node_type_select.move(house_node_card)
                    node_house_select.move(house_node_card)
                    node_error.move(house_node_card)
                    with ui.row().classes("q-mt-md justify-end q-gutter-sm"):
                        ui.button("Cancel", on_click=node_dialog.close).props("flat")
                        ui.button(
                            "Save",
                            color="primary",
                            on_click=lambda: ui.timer(0, save_node, once=True),
                        ).props("unelevated")

                async def on_election_change() -> None:
                    state["election_id"] = election_select.value or ""
                    state["validation"] = None
                    await refresh_configuration()
                    await refresh_candidates()
                    render_validation()

                election_select.on(
                    "update:model-value",
                    lambda: ui.timer(0, on_election_change, once=True),
                )
                ui.timer(0.1, load_elections, once=True)
