"""Election management page."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.services.auth_service import AuthService
from app.services.election_service import ElectionService
from app.theme import apply_saved_theme, inject_theme

ROLE_CAN_EDIT = {"Administrator", "Super Administrator"}
STATUS_COLORS = {
    "Draft": "grey",
    "Published": "info",
    "Live": "positive",
    "Paused": "orange",
    "Completed": "warning",
    "Archived": "negative",
}


def _can_edit() -> bool:
    return AuthService.get_user().get("role") in ROLE_CAN_EDIT


def register_elections_routes() -> None:
    """Register the election management page."""

    @ui.page("/elections")
    @require_auth
    def elections_page() -> None:
        inject_theme()
        apply_saved_theme()

        state: dict[str, Any] = {
            "elections": [],
            "selected_id": "",
            "detail": None,
            "versions": [],
            "validation": None,
            "search": "",
            "status_filter": "all",
        }

        with admin_shell("/elections") as content:
            with content:
                with ui.row().classes("items-center justify-between q-mb-lg w-full"):
                    with ui.column().classes("gap-0"):
                        ui.label("Election Management").classes("emp-page-title")
                        ui.label(
                            "Create, publish, and manage election lifecycles."
                        ).classes("emp-page-subtitle")

                    if _can_edit():
                        ui.button("Create Election", icon="add", on_click=lambda: open_form_dialog()).props(
                            "unelevated color=primary"
                        )

                if not AuthService.has_backend_token():
                    ui.label(
                        "No backend API token in session. Connect to the API with valid credentials "
                        "to manage elections."
                    ).classes("text-warning text-caption q-mb-md")

                with ui.row().classes("w-full q-col-gutter-md q-mb-md items-end"):
                    search_input = ui.input("Search", placeholder="Search by name or year").props(
                        "outlined dense clearable"
                    ).classes("col-12 col-md-4")
                    status_filter = ui.select(
                        label="Status",
                        options={
                            "all": "All",
                            "Draft": "Draft",
                            "Published": "Published",
                            "Live": "Live",
                            "Paused": "Paused",
                            "Completed": "Completed",
                            "Archived": "Archived",
                        },
                        value="all",
                    ).props("outlined dense").classes("col-12 col-md-3")

                list_container = ui.row().classes("w-full q-col-gutter-md")
                detail_container = ui.column().classes("w-full q-mt-lg q-gutter-md")

                editing_id: dict[str, str | None] = {"value": None}

                with ui.dialog() as form_dialog, ui.card().classes("q-pa-md").style("min-width: 420px"):
                    form_title = ui.label("Create Election").classes("text-h6 q-mb-md")
                    form_error = ui.label("").classes("text-negative text-caption")
                    form_error.visible = False
                    form_name = ui.input("Election Name").props("outlined dense").classes("w-full")
                    form_year = ui.input("Academic Year", placeholder="e.g. 2026-2027").props(
                        "outlined dense"
                    ).classes("w-full")
                    form_description = ui.textarea("Description").props("outlined autogrow").classes("w-full")
                    with ui.row().classes("justify-end q-gutter-sm q-mt-md"):
                        ui.button("Cancel", on_click=form_dialog.close).props("flat")
                        ui.button("Save", on_click=lambda: ui.timer(0, save_election, once=True)).props(
                            "unelevated color=primary"
                        )

                def _filtered_elections() -> list[dict[str, Any]]:
                    items = state["elections"]
                    if state["status_filter"] != "all":
                        items = [item for item in items if item.get("status") == state["status_filter"]]
                    search = state["search"].strip().lower()
                    if search:
                        items = [
                            item
                            for item in items
                            if search in (item.get("name") or "").lower()
                            or search in (item.get("academic_year") or "").lower()
                        ]
                    return items

                def _status_badge(status: str) -> str:
                    return STATUS_COLORS.get(status, "grey")

                async def load_elections() -> None:
                    status = None if state["status_filter"] == "all" else state["status_filter"]
                    success, message, elections = await ElectionService.list_elections(
                        status=status,
                        search=state["search"] or None,
                    )
                    if not success:
                        ui.notify(message or "Could not load elections", type="warning")
                        return
                    state["elections"] = elections
                    if elections and not state["selected_id"]:
                        state["selected_id"] = elections[0]["id"]
                    render_list()
                    if state["selected_id"]:
                        await load_detail(state["selected_id"])

                async def load_detail(election_id: str) -> None:
                    success, message, detail = await ElectionService.get_election(election_id)
                    if not success:
                        ui.notify(message or "Could not load election", type="warning")
                        return
                    state["detail"] = detail
                    state["selected_id"] = election_id

                    _, _, versions = await ElectionService.list_versions(election_id)
                    state["versions"] = versions

                    _, _, validation = await ElectionService.validate_election(election_id)
                    state["validation"] = validation

                    render_detail()

                def render_list() -> None:
                    list_container.clear()
                    with list_container:
                        for election in _filtered_elections():
                            election_id = election["id"]
                            is_selected = election_id == state["selected_id"]
                            card_classes = "col-12 col-md-6 col-lg-4 cursor-pointer"
                            if is_selected:
                                card_classes += " emp-card-selected"

                            with ui.card().classes(card_classes).on(
                                "click",
                                lambda _e=None, eid=election_id: ui.timer(
                                    0, lambda: load_detail(eid), once=True
                                ),
                            ):
                                with ui.row().classes("items-center justify-between w-full"):
                                    ui.label(election.get("name", "Untitled")).classes("text-subtitle1 text-weight-medium")
                                    ui.badge(election.get("status", "Draft")).props(
                                        f"color={_status_badge(election.get('status', 'Draft'))}"
                                    )
                                ui.label(f"Version {election.get('version', 0)}").classes("text-caption text-grey-7")
                                if election.get("academic_year"):
                                    ui.label(election["academic_year"]).classes("text-caption")
                                with ui.row().classes("q-gutter-sm q-mt-xs"):
                                    ui.label(f"{election.get('position_count', 0)} positions").classes("text-caption")
                                    ui.label(f"{election.get('candidate_count', 0)} candidates").classes("text-caption")
                                if election.get("configuration_locked"):
                                    with ui.row().classes("items-center q-mt-xs"):
                                        ui.icon("lock", size="xs").classes("text-warning")
                                        ui.label("Configuration locked").classes("text-caption text-warning")

                        if not _filtered_elections():
                            with ui.column().classes("col-12 items-center q-pa-lg"):
                                ui.icon("ballot", size="lg").classes("text-grey-5")
                                ui.label("No elections found").classes("text-grey-6")

                def render_detail() -> None:
                    detail_container.clear()
                    detail = state.get("detail")
                    if not detail:
                        return

                    election_id = detail["id"]
                    status = detail.get("status", "Draft")
                    locked = detail.get("configuration_locked", False)

                    with detail_container:
                        with ui.card().classes("w-full"):
                            with ui.row().classes("items-center justify-between w-full q-mb-md"):
                                with ui.column().classes("gap-0"):
                                    ui.label(detail.get("name", "")).classes("text-h6")
                                    ui.label(f"Status: {status} · Version {detail.get('version', 0)}").classes(
                                        "text-caption text-grey-7"
                                    )
                                    ui.label(f"Election ID: {election_id}").classes(
                                        "text-caption text-grey-6"
                                    ).style("font-family: monospace; user-select: all;")
                                ui.badge(status).props(f"color={_status_badge(status)}")

                            if detail.get("description"):
                                ui.label(detail["description"]).classes("text-body2 q-mb-md")

                            with ui.row().classes("q-gutter-md q-mb-md"):
                                ui.label(f"Regular positions: {detail.get('regular_position_count', 0)}").classes(
                                    "text-caption"
                                )
                                ui.label(f"House positions: {detail.get('house_position_count', 0)}").classes(
                                    "text-caption"
                                )
                                ui.label(f"Candidates: {detail.get('candidate_count', 0)}").classes("text-caption")
                                if locked:
                                    with ui.row().classes("items-center"):
                                        ui.icon("lock", size="xs").classes("text-warning")
                                        ui.label("Locked").classes("text-caption text-warning")

                            if _can_edit():
                                with ui.row().classes("q-gutter-sm flex-wrap"):
                                    if status in {"Draft", "Published"}:
                                        ui.button("Edit", icon="edit", on_click=lambda: open_form_dialog(detail)).props(
                                            "outline"
                                        )
                                    ui.button("Validate", icon="fact_check", on_click=lambda: run_validate(election_id)).props(
                                        "outline"
                                    )
                                    if status in {"Draft", "Published"}:
                                        ui.button(
                                            "Publish",
                                            icon="publish",
                                            on_click=lambda: run_publish(election_id),
                                        ).props("unelevated color=primary")
                                    if not locked and status in {"Draft", "Published"}:
                                        ui.button("Lock", icon="lock", on_click=lambda: run_lock(election_id)).props(
                                            "outline"
                                        )
                                    if locked and status not in {"Live", "Paused", "Archived"}:
                                        ui.button(
                                            "Unlock",
                                            icon="lock_open",
                                            on_click=lambda: run_unlock(election_id),
                                        ).props("outline")
                                    ui.button(
                                        "Duplicate",
                                        icon="content_copy",
                                        on_click=lambda: run_duplicate(election_id),
                                    ).props("outline")
                                    if status == "Published":
                                        ui.button(
                                            "Start Voting",
                                            icon="play_arrow",
                                            on_click=lambda: run_start(election_id),
                                        ).props("unelevated color=positive")
                                    if status == "Live":
                                        ui.button(
                                            "Pause Voting",
                                            icon="pause",
                                            on_click=lambda: run_pause(election_id),
                                        ).props("unelevated color=warning")
                                        ui.button(
                                            "End Voting",
                                            icon="stop",
                                            on_click=lambda: confirm_end_election(election_id, detail.get("name", "")),
                                        ).props("unelevated color=negative")
                                    if status == "Paused":
                                        ui.button(
                                            "Resume Voting",
                                            icon="play_arrow",
                                            on_click=lambda: run_resume(election_id),
                                        ).props("unelevated color=positive")
                                        ui.button(
                                            "End Voting",
                                            icon="stop",
                                            on_click=lambda: confirm_end_election(election_id, detail.get("name", "")),
                                        ).props("unelevated color=negative")
                                    if status in {"Completed", "Published"}:
                                        ui.button(
                                            "Archive",
                                            icon="archive",
                                            on_click=lambda: run_archive(election_id),
                                        ).props("outline")
                                    if status in {"Draft", "Completed", "Archived"}:
                                        ui.button(
                                            "Delete",
                                            icon="delete",
                                            on_click=lambda: confirm_delete_election(
                                                election_id, detail.get("name", ""), status
                                            ),
                                        ).props("outline color=negative")

                        validation = state.get("validation")
                        if validation:
                            with ui.card().classes("w-full"):
                                ui.label("Validation").classes("text-subtitle1 q-mb-sm")
                                if validation.get("valid"):
                                    ui.label("Election is ready to publish.").classes("text-positive")
                                else:
                                    for error in validation.get("errors", []):
                                        ui.label(f"• {error}").classes("text-negative text-caption")

                        versions = state.get("versions") or []
                        with ui.card().classes("w-full"):
                            ui.label("Published Versions").classes("text-subtitle1 q-mb-sm")
                            if not versions:
                                ui.label("No published versions yet.").classes("text-caption text-grey-6")
                            else:
                                for version in versions:
                                    with ui.row().classes("items-center justify-between w-full q-py-xs"):
                                        with ui.column().classes("gap-0"):
                                            ui.label(f"Version {version.get('version')}").classes("text-body2")
                                            ui.label(version.get("checksum", "")[:16] + "...").classes(
                                                "text-caption text-grey-6"
                                            )
                                        size = version.get("package_size")
                                        size_label = f"{size // 1024} KB" if size else "—"
                                        ui.label(size_label).classes("text-caption")

                def open_form_dialog(election: dict[str, Any] | None = None) -> None:
                    form_error.visible = False
                    form_error.text = ""
                    if election:
                        editing_id["value"] = election["id"]
                        form_title.text = "Edit Election"
                        form_name.value = election.get("name", "")
                        form_year.value = election.get("academic_year") or ""
                        form_description.value = election.get("description") or ""
                    else:
                        editing_id["value"] = None
                        form_title.text = "Create Election"
                        form_name.value = ""
                        form_year.value = ""
                        form_description.value = ""
                    form_dialog.open()

                async def save_election() -> None:
                    form_error.visible = False
                    name = (form_name.value or "").strip()
                    if not name:
                        form_error.text = "Election name is required"
                        form_error.visible = True
                        return

                    payload = {
                        "name": name,
                        "academic_year": (form_year.value or "").strip() or None,
                        "description": (form_description.value or "").strip() or None,
                    }

                    if editing_id["value"]:
                        success, message, _ = await ElectionService.update_election(editing_id["value"], payload)
                    else:
                        success, message, data = await ElectionService.create_election(payload)
                        if success and data:
                            state["selected_id"] = data["id"]

                    if not success:
                        form_error.text = message or "Save failed"
                        form_error.visible = True
                        return

                    form_dialog.close()
                    ui.notify("Election saved", type="positive")
                    await load_elections()

                async def run_validate(election_id: str) -> None:
                    _, _, validation = await ElectionService.validate_election(election_id)
                    state["validation"] = validation
                    render_detail()
                    if validation and validation.get("valid"):
                        ui.notify("Validation passed", type="positive")
                    else:
                        ui.notify("Validation failed — see details", type="warning")

                async def run_publish(election_id: str) -> None:
                    success, message, data = await ElectionService.publish_election(election_id)
                    if not success:
                        ui.notify(message or "Publish failed", type="negative")
                        return
                    version = data.get("version") if data else "?"
                    ui.notify(f"Published as version {version}", type="positive")
                    await load_elections()

                async def run_lock(election_id: str) -> None:
                    success, message, _ = await ElectionService.lock_election(election_id)
                    ui.notify(message or ("Locked" if success else "Lock failed"), type="positive" if success else "negative")
                    if success:
                        await load_elections()

                async def run_unlock(election_id: str) -> None:
                    success, message, _ = await ElectionService.unlock_election(election_id)
                    ui.notify(
                        message or ("Unlocked" if success else "Unlock failed"),
                        type="positive" if success else "negative",
                    )
                    if success:
                        await load_elections()

                async def run_duplicate(election_id: str) -> None:
                    success, message, data = await ElectionService.duplicate_election(election_id)
                    if not success:
                        ui.notify(message or "Duplicate failed", type="negative")
                        return
                    if data:
                        state["selected_id"] = data["id"]
                    ui.notify("Election duplicated", type="positive")
                    await load_elections()

                async def run_archive(election_id: str) -> None:
                    success, message, _ = await ElectionService.archive_election(election_id)
                    ui.notify(
                        message or ("Archived" if success else "Archive failed"),
                        type="positive" if success else "negative",
                    )
                    if success:
                        await load_elections()

                async def run_start(election_id: str) -> None:
                    success, message, data = await ElectionService.start_election(election_id)
                    if success:
                        status = (data or {}).get("status", "Live")
                        ui.notify(
                            message or (f"Election is {status}" if status == "Live" else "Started"),
                            type="positive",
                        )
                    else:
                        ui.notify(message or "Start failed", type="negative")
                    # Always refresh so a stale Published badge can't hide Live status.
                    await load_elections()

                async def run_pause(election_id: str) -> None:
                    success, message, data = await ElectionService.pause_election(election_id)
                    if success:
                        status = (data or {}).get("status", "Paused")
                        ui.notify(message or f"Election is {status}", type="warning")
                    else:
                        ui.notify(message or "Pause failed", type="negative")
                    await load_elections()

                async def run_resume(election_id: str) -> None:
                    success, message, data = await ElectionService.resume_election(election_id)
                    if success:
                        status = (data or {}).get("status", "Live")
                        ui.notify(message or f"Election is {status}", type="positive")
                    else:
                        ui.notify(message or "Resume failed", type="negative")
                    await load_elections()

                def confirm_end_election(election_id: str, election_name: str) -> None:
                    """Ask for explicit confirmation before permanently ending voting."""
                    name = (election_name or "").strip() or "this election"
                    with ui.dialog() as confirm_dialog, ui.card().classes("q-pa-md").style("min-width: 420px"):
                        ui.label("End voting?").classes("text-h6 q-mb-sm")
                        ui.label(
                            f'You are about to permanently end voting for "{name}".'
                        ).classes("text-body2 q-mb-sm")
                        ui.label(
                            "This cannot be undone from Pause/Resume. "
                            "After ending, the election status becomes Completed."
                        ).classes("text-caption text-grey-7 q-mb-md")
                        with ui.row().classes("justify-end q-gutter-sm w-full"):
                            ui.button("Cancel", on_click=confirm_dialog.close).props("flat")
                            ui.button(
                                "Yes, End Voting",
                                icon="stop",
                                on_click=lambda: ui.timer(
                                    0,
                                    lambda: _confirm_and_end(election_id, confirm_dialog),
                                    once=True,
                                ),
                            ).props("unelevated color=negative")
                    confirm_dialog.open()

                async def _confirm_and_end(election_id: str, confirm_dialog) -> None:
                    confirm_dialog.close()
                    await run_end(election_id)

                async def run_end(election_id: str) -> None:
                    success, message, data = await ElectionService.end_election(election_id)
                    if success:
                        status = (data or {}).get("status", "Completed")
                        election_name = (data or {}).get("name") or "Election"
                        ui.notify(
                            message
                            or f'"{election_name}" has ended. Status is now {status}.',
                            type="positive",
                        )
                    else:
                        ui.notify(message or "End failed", type="negative")
                    # Always refresh so a stale Live badge can't hide Completed status.
                    await load_elections()

                def confirm_delete_election(
                    election_id: str,
                    election_name: str,
                    status: str = "Draft",
                ) -> None:
                    """Ask for explicit confirmation before deleting an election."""
                    name = (election_name or "").strip() or "this election"
                    with ui.dialog() as confirm_dialog, ui.card().classes("q-pa-md").style("min-width: 420px"):
                        ui.label("Delete election?").classes("text-h6 q-mb-sm")
                        ui.label(
                            f'You are about to permanently delete "{name}" ({status}).'
                        ).classes("text-body2 q-mb-sm")
                        ui.label(
                            "This cannot be undone. Live or paused elections must be ended first."
                        ).classes("text-caption text-grey-7 q-mb-md")
                        with ui.row().classes("justify-end q-gutter-sm w-full"):
                            ui.button("Cancel", on_click=confirm_dialog.close).props("flat")
                            ui.button(
                                "Yes, Delete",
                                icon="delete",
                                on_click=lambda: ui.timer(
                                    0,
                                    lambda: _confirm_and_delete(election_id, name, confirm_dialog),
                                    once=True,
                                ),
                            ).props("unelevated color=negative")
                    confirm_dialog.open()

                async def _confirm_and_delete(election_id: str, election_name: str, confirm_dialog) -> None:
                    confirm_dialog.close()
                    await run_delete(election_id, election_name)

                async def run_delete(election_id: str, election_name: str = "") -> None:
                    success, message = await ElectionService.delete_election(election_id)
                    if not success:
                        ui.notify(message or "Delete failed", type="negative")
                        return
                    state["selected_id"] = ""
                    state["detail"] = None
                    name = (election_name or "").strip() or "Election"
                    ui.notify(f'"{name}" has been deleted.', type="positive")
                    await load_elections()

                def on_search_change() -> None:
                    state["search"] = search_input.value or ""
                    ui.timer(0, load_elections, once=True)

                def on_status_change() -> None:
                    state["status_filter"] = status_filter.value
                    ui.timer(0, load_elections, once=True)

                search_input.on("update:model-value", lambda: on_search_change())
                status_filter.on("update:model-value", lambda: on_status_change())

                ui.timer(0, load_elections, once=True)
