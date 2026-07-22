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
            "elections": [],
            "houses": [],
            "configuration": None,
            "candidates": [],
            "nodes": [],
            "selected_house_id": "",
            "validation": None,
        }
        election_buttons: ui.row

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

                ui.label("Election").classes("text-caption text-grey-7 q-mb-xs")
                election_buttons = ui.row().classes("w-full q-gutter-sm q-mb-md flex-wrap")

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
                node_house_select = ui.select(options={}, label="Assigned House").props(
                    "outlined dense emit-value map-options"
                ).classes("w-full")
                editing_node_id: dict[str, str | None] = {"value": None}

                def render_election_buttons() -> None:
                    election_buttons.clear()
                    with election_buttons:
                        if not state["elections"]:
                            ui.label("No elections available.").classes("text-caption text-grey-6")
                            return
                        for election in state["elections"]:
                            election_id = election["id"]
                            label = election.get("election_name") or election.get("name", "Election")
                            status = election.get("status", "")
                            button_label = f"{label} ({status})" if status else label
                            is_selected = election_id == state["election_id"]
                            props = "unelevated color=primary" if is_selected else "outline color=primary"

                            def _make_handler(eid: str = election_id):
                                async def _handler() -> None:
                                    if state["election_id"] == eid:
                                        return
                                    state["election_id"] = eid
                                    state["validation"] = None
                                    render_election_buttons()
                                    await refresh_all()
                                    render_validation()

                                return _handler

                            ui.button(button_label, on_click=_make_handler()).props(props)

                async def load_elections() -> None:
                    success, message, elections = await HouseService.list_elections()
                    if not success:
                        ui.notify(message or "Could not load elections", type="warning")
                        state["elections"] = []
                        render_election_buttons()
                        render_houses()
                        return

                    state["elections"] = elections
                    valid_ids = {item["id"] for item in elections}
                    if not elections:
                        state["election_id"] = ""
                    elif state["election_id"] not in valid_ids:
                        state["election_id"] = elections[0]["id"]
                    render_election_buttons()
                    await refresh_all()

                async def refresh_houses() -> None:
                    success, message, houses = await HouseService.list_houses()
                    if success:
                        state["houses"] = houses
                        house_options = {house["id"]: house["house_name"] for house in houses}
                        candidate_house_select.set_options(
                            house_options,
                            value=candidate_house_select.value
                            if candidate_house_select.value in house_options
                            else next(iter(house_options), None),
                        )
                        node_house_select.set_options(
                            house_options,
                            value=node_house_select.value
                            if node_house_select.value in house_options
                            else next(iter(house_options), None),
                        )
                        if house_options and not state["selected_house_id"]:
                            state["selected_house_id"] = next(iter(house_options))
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
                    success, message, nodes = await HouseService.list_nodes(election_type="House")
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
                    house_nodes = [
                        node for node in state["nodes"] if node.get("election_type") == "House"
                    ]
                    house_options = {
                        house["id"]: house["house_name"] for house in state["houses"]
                    }
                    if house_options:
                        node_house_select.set_options(house_options, value=node_house_select.value)

                    filtered = house_nodes
                    if state["selected_house_id"]:
                        filtered = [
                            node
                            for node in house_nodes
                            if node.get("house_id") == state["selected_house_id"]
                        ]

                    with nodes_panel:
                        ui.label(
                            "Register house voting machines here. Switch houses below to view and assign "
                            "nodes for Pallava, Pandya, Chera, and Chola. Regular election nodes are managed "
                            "under Regular Election."
                        ).classes("text-body2 text-grey-7 q-mb-md")

                        with ui.row().classes("w-full items-center q-gutter-sm q-mb-md flex-wrap"):
                            def _select_house(house_id: str) -> None:
                                state["selected_house_id"] = house_id
                                render_nodes()

                            all_props = "unelevated" if not state["selected_house_id"] else "outline"
                            ui.button(
                                "All Houses",
                                on_click=lambda: _select_house(""),
                            ).props(f"{all_props} dense").classes("q-mb-xs")

                            for house in state["houses"]:
                                house_id = house["id"]
                                is_active = state["selected_house_id"] == house_id
                                props = "unelevated" if is_active else "outline"
                                ui.button(
                                    house.get("house_name", "House"),
                                    on_click=lambda hid=house_id: _select_house(hid),
                                ).props(f"{props} dense color=primary").classes("q-mb-xs")

                            ui.space()
                            if _can_edit():
                                ui.button(
                                    "Register Node",
                                    icon="add",
                                    color="primary",
                                    on_click=open_create_node_dialog,
                                ).props("unelevated")

                        if filtered:
                            for node in filtered:
                                _render_node_card(node)
                        else:
                            with ui.element("div").classes("emp-placeholder w-full"):
                                ui.icon("computer", size="xl").classes("text-grey-5 q-mb-md")
                                selected_name = house_options.get(state["selected_house_id"], "")
                                empty_label = (
                                    f"No voting nodes for {selected_name} yet."
                                    if selected_name
                                    else "No house voting nodes assigned yet."
                                )
                                ui.label(empty_label).classes("text-h6 text-weight-medium")
                                if selected_name and _can_edit():
                                    ui.label(
                                        f'Click "Register Node" to add a machine for {selected_name}.'
                                    ).classes("text-caption text-grey-6")

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
                                with ui.row().classes("q-gutter-xs"):
                                    ui.button(
                                        icon="edit",
                                        on_click=lambda n=node: open_edit_node_dialog(n),
                                    ).props("flat round dense color=primary")
                                    ui.button(
                                        icon="delete",
                                        on_click=lambda n=node: delete_node(n),
                                    ).props("flat round dense color=negative")

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

                def open_create_node_dialog() -> None:
                    editing_node_id["value"] = None
                    node_dialog_title.text = "Register House Node"
                    node_error.visible = False
                    node_name_input.value = ""
                    house_options = {
                        house["id"]: house["house_name"] for house in state["houses"]
                    }
                    default_house = state["selected_house_id"] or next(iter(house_options), None)
                    node_house_select.set_options(house_options, value=default_house)
                    node_dialog.open()

                def open_edit_node_dialog(node: dict[str, Any]) -> None:
                    editing_node_id["value"] = node["id"]
                    node_dialog_title.text = "Edit House Node"
                    node_error.visible = False
                    node_name_input.value = node.get("node_name", "")
                    house_options = {
                        house["id"]: house["house_name"] for house in state["houses"]
                    }
                    node_house_select.set_options(
                        house_options,
                        value=node.get("house_id") or next(iter(house_options), None),
                    )
                    node_dialog.open()

                async def delete_node(node: dict[str, Any]) -> None:
                    with ui.dialog() as confirm_dialog, ui.card().classes("q-pa-md"):
                        ui.label("Delete Node?").classes("text-h6")
                        ui.label(
                            f'Remove "{node.get("node_name", "")}"? '
                            "It will be deactivated and can no longer sync votes."
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

                    success, message = await HouseService.delete_node(node["id"])
                    if success:
                        ui.notify("Node deleted", type="positive")
                        await refresh_nodes()
                    else:
                        ui.notify(message or "Could not delete node", type="negative")

                def show_node_credentials(registration: dict[str, Any]) -> None:
                    node_id_value.set_text(registration.get("id") or "")
                    node_secret_value.set_text(registration.get("node_secret") or "")
                    credentials_dialog.open()

                async def copy_text(label: str, value: str) -> None:
                    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
                    await ui.run_javascript(f"navigator.clipboard.writeText('{escaped}')")
                    ui.notify(f"{label} copied", type="positive")

                async def copy_node_id() -> None:
                    await copy_text("Node ID", node_id_value.text or "")

                async def copy_node_secret() -> None:
                    await copy_text("Node Secret", node_secret_value.text or "")

                async def save_node() -> None:
                    node_error.visible = False
                    name = (node_name_input.value or "").strip()
                    if not name:
                        node_error.text = "Node name is required."
                        node_error.visible = True
                        return
                    if not node_house_select.value:
                        node_error.text = "Assigned house is required for House nodes."
                        node_error.visible = True
                        return

                    payload: dict[str, Any] = {
                        "node_name": name,
                        "election_type": "House",
                        "house_id": node_house_select.value,
                    }

                    if editing_node_id["value"]:
                        success, message, _ = await HouseService.update_node(editing_node_id["value"], payload)
                        if success:
                            node_dialog.close()
                            ui.notify("Node assignment saved", type="positive")
                            await refresh_nodes()
                        else:
                            node_error.text = message or "Could not save node assignment"
                            node_error.visible = True
                        return

                    payload["active"] = True
                    success, message, registration = await HouseService.create_node(payload)
                    if success and registration:
                        node_dialog.close()
                        ui.notify("Node registered", type="positive")
                        await refresh_nodes()
                        show_node_credentials(registration)
                    else:
                        node_error.text = message or "Could not register node"
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
                    node_dialog_title = ui.label("Register House Node").classes("text-h6 q-mb-md")
                    node_name_input.move(house_node_card)
                    node_house_select.move(house_node_card)
                    node_error.move(house_node_card)
                    with ui.row().classes("q-mt-md justify-end q-gutter-sm"):
                        ui.button("Cancel", on_click=node_dialog.close).props("flat")
                        ui.button(
                            "Save",
                            color="primary",
                            on_click=lambda: ui.timer(0, save_node, once=True),
                        ).props("unelevated")

                credentials_dialog = ui.dialog().props("persistent")
                with credentials_dialog, ui.card().classes("q-pa-md").style("min-width: 480px"):
                    ui.label("Save Node Credentials").classes("text-h6")
                    ui.label(
                        "Copy these values now. The Node Secret is shown only once and cannot be recovered later."
                    ).classes("text-body2 text-warning q-mt-sm q-mb-md")
                    ui.label("Node ID").classes("text-caption text-grey-7")
                    with ui.row().classes("w-full items-center q-gutter-sm q-mb-md"):
                        node_id_value = ui.label("").classes("text-body2 text-weight-medium").style(
                            "word-break: break-all; flex: 1"
                        )
                        ui.button(
                            icon="content_copy",
                            on_click=lambda: ui.timer(0, copy_node_id, once=True),
                        ).props("flat round dense")
                    ui.label("Node Secret").classes("text-caption text-grey-7")
                    with ui.row().classes("w-full items-center q-gutter-sm q-mb-md"):
                        node_secret_value = ui.label("").classes("text-body2 text-weight-medium").style(
                            "word-break: break-all; flex: 1"
                        )
                        ui.button(
                            icon="content_copy",
                            on_click=lambda: ui.timer(0, copy_node_secret, once=True),
                        ).props("flat round dense")
                    ui.label(
                        "Enter both on the voting PC under Admin → Node Config."
                    ).classes("text-caption text-grey-7 q-mb-md")
                    with ui.row().classes("justify-end"):
                        ui.button(
                            "I've saved these",
                            color="primary",
                            on_click=credentials_dialog.close,
                        ).props("unelevated")

                ui.timer(0.1, load_elections, once=True)
