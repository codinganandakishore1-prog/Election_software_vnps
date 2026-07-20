"""Reports generation and download page."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.services.auth_service import AuthService
from app.services.election_service import ElectionService
from app.services.report_service import ReportService
from app.theme import apply_saved_theme, inject_theme

REPORT_FORMATS = (
    ("Excel", "Excel (.xlsx)"),
    ("CSV", "CSV (.csv)"),
    ("PDF", "PDF (.pdf)"),
)
ROLE_CAN_GENERATE = {"Administrator", "Super Administrator"}


def _can_generate() -> bool:
    return AuthService.get_user().get("role") in ROLE_CAN_GENERATE


def register_reports_routes() -> None:
    """Register the reports page."""

    @ui.page("/reports")
    @require_auth
    def reports_page() -> None:
        inject_theme()
        apply_saved_theme()

        state: dict[str, Any] = {
            "election_id": "",
            "elections": [],
            "reports": [],
            "format": "Excel",
        }

        with admin_shell("/reports") as content:
            with content:
                with ui.row().classes("items-center justify-between q-mb-lg w-full"):
                    with ui.column().classes("gap-0"):
                        ui.label("Reports").classes("emp-page-title")
                        ui.label("Generate and download official election reports.").classes(
                            "emp-page-subtitle"
                        )

                if not AuthService.has_backend_token():
                    ui.label(
                        "No backend API token in session. Connect to the API with valid credentials "
                        "to generate reports."
                    ).classes("text-warning text-caption q-mb-md")

                ui.label("Election").classes("text-caption text-grey-7 q-mb-xs")
                election_buttons = ui.row().classes("w-full q-gutter-sm q-mb-md flex-wrap")

                ui.label("Format").classes("text-caption text-grey-7 q-mb-xs")
                format_buttons = ui.row().classes("w-full q-gutter-sm q-mb-md flex-wrap")

                generate_slot = ui.row().classes("w-full q-mb-md")
                list_container = ui.column().classes("w-full q-gutter-sm")

                def render_election_buttons() -> None:
                    election_buttons.clear()
                    with election_buttons:
                        if not state["elections"]:
                            ui.label("No elections available.").classes("text-caption text-grey-6")
                            return
                        for election in state["elections"]:
                            election_id = election["id"]
                            label = election.get("name") or election.get("election_name", "Election")
                            status = election.get("status", "")
                            button_label = f"{label} ({status})" if status else label
                            is_selected = election_id == state["election_id"]
                            props = "unelevated color=primary" if is_selected else "outline color=primary"

                            def _make_handler(eid: str = election_id):
                                async def _handler() -> None:
                                    if state["election_id"] == eid:
                                        return
                                    await select_election(eid)

                                return _handler

                            ui.button(button_label, on_click=_make_handler()).props(props)

                def render_format_buttons() -> None:
                    format_buttons.clear()
                    with format_buttons:
                        for value, label in REPORT_FORMATS:
                            is_selected = value == state["format"]
                            props = "unelevated color=primary" if is_selected else "outline color=primary"

                            def _make_handler(selected: str = value):
                                def _handler() -> None:
                                    state["format"] = selected
                                    render_format_buttons()

                                return _handler

                            ui.button(label, on_click=_make_handler()).props(props)

                def render_reports() -> None:
                    list_container.clear()
                    with list_container:
                        if not state["reports"]:
                            with ui.element("div").classes("emp-placeholder w-full"):
                                ui.icon("description", size="xl").classes("text-grey-5 q-mb-md")
                                ui.label("No reports generated yet").classes(
                                    "text-h6 text-weight-medium"
                                )
                                ui.label(
                                    "Generate a report to download Excel, CSV, or PDF exports."
                                ).classes("text-caption text-grey-6")
                            return

                        for report in state["reports"]:
                            with ui.element("div").classes("emp-card q-pa-md w-full"):
                                with ui.row().classes("items-center justify-between w-full q-gutter-sm"):
                                    with ui.column().classes("gap-0 col-grow"):
                                        ui.label(report.get("report_name", "Report")).classes(
                                            "text-subtitle1"
                                        )
                                        ui.label(
                                            f'{report.get("report_type", "—")} · '
                                            f'{report.get("generated_at", "—")}'
                                        ).classes("text-caption text-grey-7")
                                        if report.get("generated_by_name"):
                                            ui.label(f'By {report["generated_by_name"]}').classes(
                                                "text-caption"
                                            )

                                    with ui.row().classes("items-center q-gutter-sm no-wrap"):
                                        def _make_download(selected: dict[str, Any] = report):
                                            async def _handler() -> None:
                                                await download_report(selected)

                                            return _handler

                                        ui.button(
                                            "Download",
                                            icon="download",
                                            on_click=_make_download(),
                                        ).props("outline")

                                        if _can_generate():
                                            def _make_delete(selected: dict[str, Any] = report):
                                                async def _handler() -> None:
                                                    await delete_report(selected)

                                                return _handler

                                            ui.button(
                                                "Delete",
                                                icon="delete",
                                                on_click=_make_delete(),
                                            ).props("outline color=negative")

                async def select_election(election_id: str) -> None:
                    state["election_id"] = election_id
                    render_election_buttons()
                    await refresh_reports()

                async def load_elections() -> None:
                    success, message, elections = await ElectionService.list_elections()
                    if not success:
                        ui.notify(message or "Could not load elections", type="negative")
                        render_election_buttons()
                        render_format_buttons()
                        return
                    state["elections"] = elections
                    if elections and (
                        not state["election_id"]
                        or state["election_id"] not in {e["id"] for e in elections}
                    ):
                        state["election_id"] = elections[0]["id"]
                    render_election_buttons()
                    render_format_buttons()
                    await refresh_reports()

                async def refresh_reports() -> None:
                    success, message, reports = await ReportService.list_reports(
                        election_id=state["election_id"] or None,
                    )
                    if success:
                        state["reports"] = reports
                    else:
                        state["reports"] = []
                        if message:
                            ui.notify(message, type="negative")
                    render_reports()

                async def download_report(report: dict[str, Any]) -> None:
                    success, message, content, content_type = await ReportService.download_report(
                        report["id"]
                    )
                    if not success or content is None:
                        ui.notify(message or "Download failed", type="negative")
                        return
                    extension = {
                        "Excel": ".xlsx",
                        "CSV": ".csv",
                        "PDF": ".pdf",
                    }.get(report.get("report_type", ""), ".bin")
                    filename = f'{report.get("report_name", "report")}{extension}'
                    ui.download(
                        content,
                        filename,
                        media_type=content_type or "application/octet-stream",
                    )

                async def delete_report(report: dict[str, Any]) -> None:
                    report_id = report.get("id")
                    if not report_id:
                        ui.notify("Report id missing", type="negative")
                        return
                    success, message = await ReportService.delete_report(report_id)
                    if success:
                        ui.notify("Report deleted", type="positive")
                        await refresh_reports()
                    else:
                        ui.notify(message or "Delete failed", type="negative")

                async def generate_report() -> None:
                    if not state["election_id"]:
                        ui.notify("Select an election first", type="warning")
                        return
                    success, message, report = await ReportService.generate_report(
                        state["election_id"],
                        state["format"] or "Excel",
                    )
                    if not success:
                        ui.notify(message or "Report generation failed", type="negative")
                        return

                    ui.notify("Report generated", type="positive")
                    await refresh_reports()
                    if isinstance(report, dict) and report.get("id"):
                        await download_report(report)

                if _can_generate():
                    with generate_slot:
                        ui.button(
                            "Generate Report",
                            icon="description",
                            on_click=generate_report,
                        ).props("unelevated color=primary")

                render_format_buttons()
                ui.timer(0.1, load_elections, once=True)
