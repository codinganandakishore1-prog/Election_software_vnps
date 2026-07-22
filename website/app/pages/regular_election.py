"""Regular election configuration page."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.services.auth_service import AuthService
from app.services.candidate_service import CandidateService
from app.services.election_service import ElectionService
from app.services.house_service import HouseService
from app.services.position_service import PositionService
from app.theme import apply_saved_theme, inject_theme

ROLE_CAN_EDIT = {"Administrator", "Super Administrator"}
POSITIONS_TAB = "Positions"
CANDIDATES_TAB = "Candidates"
NODES_TAB = "Node Assignment"
VALIDATION_TAB = "Validation"
TABS = (POSITIONS_TAB, CANDIDATES_TAB, NODES_TAB, VALIDATION_TAB)


def _can_edit() -> bool:
    return AuthService.get_user().get("role") in ROLE_CAN_EDIT


def register_regular_election_routes() -> None:
    """Register the regular election management page."""

    @ui.page("/regular-election")
    @require_auth
    def regular_election_page() -> None:
        inject_theme()
        apply_saved_theme()

        state: dict[str, Any] = {
            "election_id": "",
            "elections": [],
            "positions": [],
            "candidates": [],
            "nodes": [],
            "validation": None,
        }
        election_buttons: ui.row

        with admin_shell("/regular-election") as content:
            with content:
                with ui.row().classes("items-center justify-between q-mb-lg w-full"):
                    with ui.column().classes("gap-0"):
                        ui.label("Regular Election").classes("emp-page-title")
                        ui.label("Configure positions, candidates, and regular voting nodes.").classes(
                            "emp-page-subtitle"
                        )

                if not AuthService.has_backend_token():
                    ui.label(
                        "No backend API token in session. Connect to the API with valid credentials "
                        "to manage the regular election."
                    ).classes("text-warning text-caption q-mb-md")

                ui.label("Election").classes("text-caption text-grey-7 q-mb-xs")
                election_buttons = ui.row().classes("w-full q-gutter-sm q-mb-md flex-wrap")

                tabs = ui.tabs().classes("w-full")
                with tabs:
                    for tab_name in TABS:
                        ui.tab(tab_name)

                with ui.tab_panels(tabs, value=POSITIONS_TAB).classes("w-full q-mt-md"):
                    with ui.tab_panel(POSITIONS_TAB):
                        positions_panel = ui.column().classes("w-full q-gutter-md")
                    with ui.tab_panel(CANDIDATES_TAB):
                        candidates_panel = ui.column().classes("w-full q-gutter-md")
                    with ui.tab_panel(NODES_TAB):
                        nodes_panel = ui.column().classes("w-full q-gutter-md")
                    with ui.tab_panel(VALIDATION_TAB):
                        validation_panel = ui.column().classes("w-full q-gutter-md")

                with positions_panel:
                    ui.label("Loading positions…").classes("text-caption text-grey-6")
                with candidates_panel:
                    ui.label("Loading candidates…").classes("text-caption text-grey-6")
                with nodes_panel:
                    ui.label("Loading nodes…").classes("text-caption text-grey-6")
                with validation_panel:
                    ui.label("Select an election to validate.").classes("text-caption text-grey-6")

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
                                    render_election_buttons()
                                    await refresh_all()

                                return _handler

                            ui.button(button_label, on_click=_make_handler()).props(props)

                async def load_elections() -> None:
                    success, message, elections = await ElectionService.list_elections()
                    if not success:
                        ui.notify(message or "Could not load elections", type="negative")
                        state["elections"] = []
                        render_election_buttons()
                        return
                    state["elections"] = elections
                    valid_ids = {item["id"] for item in elections}
                    if not elections:
                        state["election_id"] = ""
                    elif state["election_id"] not in valid_ids:
                        state["election_id"] = elections[0]["id"]
                    render_election_buttons()
                    await refresh_all()

                async def refresh_positions() -> None:
                    positions_panel.clear()
                    if not state["election_id"]:
                        with positions_panel:
                            ui.label("Select an election to view positions.").classes("text-caption text-grey-6")
                        return
                    success, message, positions = await PositionService.list_positions(
                        election_id=state["election_id"],
                        election_type="Regular",
                    )
                    if not success:
                        ui.notify(message or "Could not load positions", type="negative")
                    state["positions"] = positions if success else []
                    with positions_panel:
                        if _can_edit():
                            ui.button(
                                "Manage Positions",
                                icon="open_in_new",
                                on_click=lambda: ui.navigate.to("/positions"),
                            ).props("outline").classes("self-start q-mb-sm")
                        if not state["positions"]:
                            with ui.element("div").classes("emp-placeholder w-full"):
                                ui.icon("badge", size="xl").classes("text-grey-5 q-mb-md")
                                ui.label("No regular positions configured yet.").classes(
                                    "text-h6 text-weight-medium"
                                )
                            return
                        for position in state["positions"]:
                            with ui.card().classes("w-full"):
                                ui.label(position.get("position_name", position.get("name", "Position"))).classes(
                                    "text-subtitle1"
                                )
                                ui.label(
                                    f'Winners: {position.get("winner_count", 1)} · '
                                    f'Order: {position.get("display_order", 0)}'
                                ).classes("text-caption")

                async def refresh_candidates() -> None:
                    candidates_panel.clear()
                    if not state["election_id"]:
                        with candidates_panel:
                            ui.label("Select an election to view candidates.").classes("text-caption text-grey-6")
                        return
                    success, message, candidates = await CandidateService.list_candidates(
                        election_id=state["election_id"],
                        election_type="Regular",
                    )
                    if not success:
                        ui.notify(message or "Could not load candidates", type="negative")
                    state["candidates"] = candidates if success else []
                    with candidates_panel:
                        if _can_edit():
                            ui.button(
                                "Manage Candidates",
                                icon="open_in_new",
                                on_click=lambda: ui.navigate.to("/candidates"),
                            ).props("outline").classes("self-start q-mb-sm")
                        if not state["candidates"]:
                            with ui.element("div").classes("emp-placeholder w-full"):
                                ui.icon("groups", size="xl").classes("text-grey-5 q-mb-md")
                                ui.label("No regular candidates configured yet.").classes(
                                    "text-h6 text-weight-medium"
                                )
                            return
                        for candidate in state["candidates"]:
                            with ui.card().classes("w-full"):
                                ui.label(candidate.get("candidate_name", "Candidate")).classes("text-subtitle1")
                                class_text = candidate.get("candidate_class") or "—"
                                section_text = candidate.get("candidate_section") or "—"
                                ui.label(
                                    f'{candidate.get("position_name", "—")} · '
                                    f'Class {class_text}-{section_text}'
                                ).classes("text-caption")

                def render_nodes() -> None:
                    nodes_panel.clear()
                    with nodes_panel:
                        with ui.row().classes("w-full items-center justify-between q-mb-md"):
                            ui.label(
                                "Register regular voting machines here. These nodes are separate from "
                                "House Election nodes — manage house machines under House Election."
                            ).classes("text-body2 text-grey-7")
                            if _can_edit():
                                ui.button(
                                    "Register Node",
                                    icon="add",
                                    color="primary",
                                    on_click=open_create_node_dialog,
                                ).props("unelevated")

                        if not state["nodes"]:
                            with ui.element("div").classes("emp-placeholder w-full"):
                                ui.icon("computer", size="xl").classes("text-grey-5 q-mb-md")
                                ui.label("No regular voting nodes assigned yet.").classes(
                                    "text-h6 text-weight-medium"
                                )
                            return

                        for node in state["nodes"]:
                            with ui.element("div").classes("emp-card q-pa-md w-full q-mb-sm"):
                                with ui.row().classes("items-center justify-between w-full"):
                                    with ui.column().classes("gap-0"):
                                        ui.label(node.get("node_name", "Node")).classes("text-subtitle1")
                                        ui.label(f'Status: {node.get("status", "—")}').classes("text-caption")
                                    if _can_edit():
                                        ui.button(
                                            icon="delete",
                                            on_click=lambda n=node: delete_node(n),
                                        ).props("flat round dense color=negative")

                async def refresh_nodes() -> None:
                    success, message, nodes = await HouseService.list_nodes(election_type="Regular")
                    if not success:
                        ui.notify(message or "Could not load nodes", type="negative")
                    state["nodes"] = nodes if success else []
                    render_nodes()

                def open_create_node_dialog() -> None:
                    node_error.visible = False
                    node_name_input.value = ""
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

                    success, message, registration = await HouseService.create_node(
                        {
                            "node_name": name,
                            "election_type": "Regular",
                            "house_id": None,
                            "active": True,
                        }
                    )
                    if success and registration:
                        node_dialog.close()
                        ui.notify("Node registered", type="positive")
                        await refresh_nodes()
                        show_node_credentials(registration)
                    else:
                        node_error.text = message or "Could not register node"
                        node_error.visible = True

                node_dialog = ui.dialog()
                node_error = ui.label("").classes("text-negative text-caption")
                node_error.visible = False
                node_name_input = ui.input("Node Name").props("outlined dense").classes("w-full")
                with node_dialog, ui.card().classes("q-pa-md").style("min-width: 420px") as regular_node_card:
                    ui.label("Register Regular Node").classes("text-h6 q-mb-md")
                    node_name_input.move(regular_node_card)
                    node_error.move(regular_node_card)
                    with ui.row().classes("q-mt-md justify-end q-gutter-sm"):
                        ui.button("Cancel", on_click=node_dialog.close).props("flat")
                        ui.button(
                            "Register",
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

                async def refresh_validation() -> None:
                    validation_panel.clear()
                    if not state["election_id"]:
                        with validation_panel:
                            ui.label("Select an election to validate.").classes("text-caption text-grey-6")
                        return
                    success, message, validation = await ElectionService.validate_election(state["election_id"])
                    state["validation"] = validation if success else None
                    with validation_panel:
                        if not validation:
                            ui.label(message or "Validation unavailable").classes("text-caption")
                            return
                        ui.label("Pre-publish validation").classes("text-subtitle1")
                        for issue in validation.get("issues", []):
                            ui.label(f"• {issue}").classes("text-caption")
                        if validation.get("ready"):
                            ui.label("Configuration is ready to publish.").classes("text-positive")
                            if _can_edit():
                                ui.button(
                                    "Publish Election",
                                    icon="publish",
                                    on_click=lambda: ui.timer(0, publish_election, once=True),
                                ).props("unelevated color=primary q-mt-md")
                        else:
                            ui.label("Resolve validation issues before publishing.").classes("text-warning")

                async def publish_election() -> None:
                    if not state["election_id"]:
                        return
                    success, message, _ = await ElectionService.publish_election(state["election_id"])
                    if success:
                        ui.notify("Election published", type="positive")
                        await refresh_validation()
                    else:
                        ui.notify(message or "Publish failed", type="negative")

                async def refresh_all() -> None:
                    await refresh_positions()
                    await refresh_candidates()
                    await refresh_nodes()
                    await refresh_validation()

                ui.timer(0.1, load_elections, once=True)
