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
            "positions": [],
            "candidates": [],
            "nodes": [],
            "validation": None,
        }

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

                async def load_elections() -> None:
                    success, message, elections = await ElectionService.list_elections()
                    if not success:
                        ui.notify(message or "Could not load elections", type="negative")
                        return
                    options = {
                        election["id"]: election.get("election_name") or election.get("name", "Election")
                        for election in elections
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

                async def refresh_nodes() -> None:
                    nodes_panel.clear()
                    success, message, nodes = await HouseService.list_nodes(election_type="Regular")
                    if not success:
                        ui.notify(message or "Could not load nodes", type="negative")
                    state["nodes"] = nodes if success else []
                    with nodes_panel:
                        if not state["nodes"]:
                            with ui.element("div").classes("emp-placeholder w-full"):
                                ui.icon("computer", size="xl").classes("text-grey-5 q-mb-md")
                                ui.label("No regular voting nodes assigned yet.").classes(
                                    "text-h6 text-weight-medium"
                                )
                            return
                        for node in state["nodes"]:
                            with ui.card().classes("w-full"):
                                ui.label(node.get("node_name", "Node")).classes("text-subtitle1")
                                ui.label(f'Status: {node.get("status", "—")}').classes("text-caption")

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

                async def on_election_change() -> None:
                    state["election_id"] = election_select.value or ""
                    await refresh_all()

                election_select.on(
                    "update:model-value",
                    lambda: ui.timer(0, on_election_change, once=True),
                )
                ui.timer(0.1, load_elections, once=True)
