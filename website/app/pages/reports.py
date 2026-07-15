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

REPORT_FORMATS = {
    "Excel": "Excel (.xlsx)",
    "CSV": "CSV (.csv)",
    "PDF": "PDF (.pdf)",
}
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

        state: dict[str, Any] = {"election_id": "", "reports": []}
        list_container = ui.column().classes("w-full q-gutter-sm")

        with admin_shell("/reports") as content:
            with content:
                with ui.row().classes("items-center justify-between q-mb-lg w-full"):
                    with ui.column().classes("gap-0"):
                        ui.label("Reports").classes("emp-page-title")
                        ui.label("Generate and download official election reports.").classes("emp-page-subtitle")

                if not AuthService.has_backend_token():
                    ui.label(
                        "No backend API token in session. Connect to the API with valid credentials "
                        "to generate reports."
                    ).classes("text-warning text-caption q-mb-md")

                with ui.row().classes("w-full q-col-gutter-md q-mb-md items-end"):
                    election_select = ui.select(label="Election", options=[], with_input=True).props(
                        "outlined dense"
                    ).classes("col-12 col-md-4")
                    format_select = ui.select(label="Format", options=REPORT_FORMATS, value="Excel").props(
                        "outlined dense"
                    ).classes("col-12 col-md-3")
                    if _can_generate():
                        ui.button("Generate Report", icon="description", on_click=lambda: ui.run(generate_report())).props(
                            "unelevated color=primary"
                        ).classes("col-12 col-md-3")

                list_container

                def render_reports() -> None:
                    list_container.clear()
                    with list_container:
                        if not state["reports"]:
                            with ui.element("div").classes("emp-placeholder w-full"):
                                ui.icon("description", size="xl").classes("text-grey-5 q-mb-md")
                                ui.label("No reports generated yet").classes("text-h6 text-weight-medium")
                                ui.label("Generate a report to download Excel, CSV, or PDF exports.").classes(
                                    "text-caption text-grey-6"
                                )
                            return

                        for report in state["reports"]:
                            with ui.card().classes("w-full"):
                                with ui.row().classes("items-center justify-between w-full"):
                                    with ui.column().classes("gap-0"):
                                        ui.label(report.get("report_name", "Report")).classes("text-subtitle1")
                                        ui.label(
                                            f'{report.get("report_type", "—")} · '
                                            f'{report.get("generated_at", "—")}'
                                        ).classes("text-caption text-grey-7")
                                        if report.get("generated_by_name"):
                                            ui.label(f'By {report["generated_by_name"]}').classes("text-caption")
                                    ui.button(
                                        "Download",
                                        icon="download",
                                        on_click=lambda r=report: ui.run(download_report(r)),
                                    ).props("outline")

                async def load_elections() -> None:
                    success, message, elections = await ElectionService.list_elections()
                    if not success:
                        ui.notify(message or "Could not load elections", type="negative")
                        return
                    options = {
                        election["id"]: election.get("name", election.get("election_name", "Election"))
                        for election in elections
                    }
                    election_select.options = options
                    if options and not state["election_id"]:
                        state["election_id"] = next(iter(options))
                        election_select.value = state["election_id"]
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

                async def generate_report() -> None:
                    if not state["election_id"]:
                        ui.notify("Select an election first", type="warning")
                        return
                    success, message, _ = await ReportService.generate_report(
                        state["election_id"],
                        format_select.value or "Excel",
                    )
                    if success:
                        ui.notify("Report generated", type="positive")
                        await refresh_reports()
                    else:
                        ui.notify(message or "Report generation failed", type="negative")

                async def download_report(report: dict[str, Any]) -> None:
                    success, message, content, content_type = await ReportService.download_report(report["id"])
                    if not success or content is None:
                        ui.notify(message or "Download failed", type="negative")
                        return
                    extension = {
                        "Excel": ".xlsx",
                        "CSV": ".csv",
                        "PDF": ".pdf",
                    }.get(report.get("report_type", ""), ".bin")
                    filename = f'{report.get("report_name", "report")}{extension}'
                    ui.download(content, filename, media_type=content_type or "application/octet-stream")

                async def on_election_change() -> None:
                    state["election_id"] = election_select.value or ""
                    await refresh_reports()

                election_select.on("update:model-value", lambda: ui.run(on_election_change()))
                ui.timer(0.1, load_elections, once=True)
