"""Audit logs page with filtering and search."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from nicegui import ui

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.services.audit_log_service import AuditLogService
from app.services.auth_service import AuthService
from app.theme import apply_saved_theme, inject_theme


def _format_timestamp(value: str | None) -> str:
    if not value:
        return "—"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return value


def _summarize_details(entry: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in ("new_value", "old_value"):
        payload = entry.get(field)
        if not isinstance(payload, dict):
            continue
        for key, value in payload.items():
            if value is not None and value != "":
                parts.append(f"{key}: {value}")
    ip = entry.get("ip_address")
    if ip:
        parts.append(f"ip: {ip}")
    return "; ".join(parts) if parts else "—"


def register_audit_logs_routes() -> None:
    """Register the audit logs page."""

    @ui.page("/audit-logs")
    @require_auth
    def audit_logs_page() -> None:
        inject_theme()
        apply_saved_theme()

        state: dict[str, Any] = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 50,
            "module_filter": "all",
            "search": "",
            "modules": ["all"],
        }

        with admin_shell("/audit-logs") as content:
            with content:
                with ui.row().classes("items-center justify-between q-mb-lg w-full"):
                    with ui.column().classes("gap-0"):
                        ui.label("Audit Logs").classes("emp-page-title")
                        ui.label(
                            "Immutable record of administrator actions, elections, nodes, sync, and reports."
                        ).classes("emp-page-subtitle")

                if not AuthService.has_backend_token():
                    ui.label(
                        "No backend API token in session. Connect to the API with valid credentials "
                        "to view audit logs."
                    ).classes("text-warning text-caption q-mb-md")

                with ui.row().classes("w-full q-col-gutter-md q-mb-md items-end"):
                    module_filter = ui.select(
                        label="Module",
                        options={"all": "All modules"},
                        value="all",
                    ).props("outlined dense emit-value map-options").classes("col-12 col-md-3")

                    search_input = ui.input(
                        "Search",
                        placeholder="Search action, module, or user",
                    ).props("outlined dense clearable").classes("col-12 col-md-5")

                    refresh_button = ui.button(
                        "Refresh",
                        icon="refresh",
                        on_click=lambda: ui.timer(0, load_logs, once=True),
                    ).props("outline color=primary").classes("col-12 col-md-2")

                summary_label = ui.label("").classes("text-caption text-grey-7 q-mb-sm")
                table_container = ui.column().classes("w-full")
                pagination_row = ui.row().classes("items-center justify-between w-full q-mt-md")

                detail_dialog = ui.dialog()
                detail_title = ui.label("").classes("text-h6")
                detail_body = ui.column().classes("q-gutter-sm w-full")

                def open_detail(entry: dict[str, Any]) -> None:
                    detail_title.text = f"{entry.get('action', 'Audit Entry')}"
                    detail_body.clear()
                    with detail_body:
                        ui.label(f"Module: {entry.get('module', '—')}").classes("text-body2")
                        ui.label(f"User: {entry.get('user_name') or 'System'}").classes("text-body2")
                        ui.label(f"Time: {_format_timestamp(entry.get('created_at'))}").classes("text-body2")
                        if entry.get("ip_address"):
                            ui.label(f"IP: {entry.get('ip_address')}").classes("text-body2")
                        if entry.get("browser"):
                            ui.label(f"Browser: {entry.get('browser')}").classes("text-caption text-grey-7")
                        if entry.get("old_value"):
                            ui.label("Previous value").classes("text-caption text-weight-medium q-mt-sm")
                            ui.code(str(entry.get("old_value"))).classes("w-full")
                        if entry.get("new_value"):
                            ui.label("New value").classes("text-caption text-weight-medium q-mt-sm")
                            ui.code(str(entry.get("new_value"))).classes("w-full")
                    detail_dialog.open()

                with detail_dialog, ui.card().classes("q-pa-md").style("min-width: 480px") as audit_detail_card:
                    detail_title.move(audit_detail_card)
                    detail_body.move(audit_detail_card)
                    with ui.row().classes("justify-end w-full q-mt-md"):
                        ui.button("Close", on_click=detail_dialog.close).props("flat")

                def render_table() -> None:
                    table_container.clear()
                    with table_container:
                        if not state["items"]:
                            with ui.column().classes("items-center emp-placeholder q-mt-md"):
                                ui.icon("history", size="xl").classes("text-grey-5 q-mb-md")
                                ui.label("No audit log entries match your filters.").classes("text-body2 text-grey-6")
                            return

                        columns = [
                            {"name": "created_at", "label": "Time", "field": "created_at", "align": "left"},
                            {"name": "module", "label": "Module", "field": "module", "align": "left"},
                            {"name": "action", "label": "Action", "field": "action", "align": "left"},
                            {"name": "user_name", "label": "User", "field": "user_name", "align": "left"},
                            {"name": "details", "label": "Details", "field": "details", "align": "left"},
                        ]
                        rows = [
                            {
                                "id": item.get("id"),
                                "created_at": _format_timestamp(item.get("created_at")),
                                "module": item.get("module", ""),
                                "action": item.get("action", ""),
                                "user_name": item.get("user_name") or "System",
                                "details": _summarize_details(item),
                                "_raw": item,
                            }
                            for item in state["items"]
                        ]

                        table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full").props(
                            "flat bordered dense"
                        )
                        table.add_slot(
                            "body-cell-module",
                            r"""
                            <q-td :props="props">
                                <q-badge :color="{
                                    'Authentication': 'primary',
                                    'Elections': 'info',
                                    'Nodes': 'secondary',
                                    'Synchronization': 'warning',
                                    'Reports': 'positive'
                                }[props.value] || 'grey'" :label="props.value" />
                            </q-td>
                            """,
                        )
                        table.on(
                            "rowClick",
                            lambda event: open_detail(event.args[1]["_raw"]),
                        )

                def render_pagination() -> None:
                    pagination_row.clear()
                    with pagination_row:
                        total_pages = max(1, (state["total"] + state["page_size"] - 1) // state["page_size"])
                        ui.label(
                            f"Page {state['page']} of {total_pages} · {state['total']} total entries"
                        ).classes("text-caption text-grey-7")

                        with ui.row().classes("q-gutter-sm"):
                            prev_btn = ui.button("Previous", icon="chevron_left").props("flat dense")
                            next_btn = ui.button("Next", icon="chevron_right").props("flat dense")
                            prev_btn.enabled = state["page"] > 1
                            next_btn.enabled = state["page"] < total_pages

                            async def go_prev() -> None:
                                if state["page"] > 1:
                                    state["page"] -= 1
                                    await load_logs()

                            async def go_next() -> None:
                                total_pages_inner = max(
                                    1, (state["total"] + state["page_size"] - 1) // state["page_size"]
                                )
                                if state["page"] < total_pages_inner:
                                    state["page"] += 1
                                    await load_logs()

                            prev_btn.on("click", lambda: ui.timer(0, go_prev, once=True))
                            next_btn.on("click", lambda: ui.timer(0, go_next, once=True))

                async def load_modules() -> None:
                    success, _, modules = await AuditLogService.list_modules()
                    if not success:
                        return
                    options = {"all": "All modules"}
                    for module in modules:
                        options[module] = module
                    module_filter.options = options
                    module_filter.update()

                async def load_logs() -> None:
                    success, message, data = await AuditLogService.list_audit_logs(
                        module=state["module_filter"],
                        search=state["search"] or None,
                        page=state["page"],
                        page_size=state["page_size"],
                    )
                    if not success or not data:
                        state["items"] = []
                        state["total"] = 0
                        summary_label.text = message or "Unable to load audit logs."
                        render_table()
                        render_pagination()
                        return

                    state["items"] = data.get("items", [])
                    state["total"] = data.get("total", 0)
                    summary_label.text = f"Showing {len(state['items'])} of {state['total']} audit log entries"
                    render_table()
                    render_pagination()

                async def on_module_change() -> None:
                    state["module_filter"] = module_filter.value or "all"
                    state["page"] = 1
                    await load_logs()

                async def on_search_change() -> None:
                    state["search"] = search_input.value or ""
                    state["page"] = 1
                    await load_logs()

                module_filter.on(
                    "update:model-value",
                    lambda: ui.timer(0, on_module_change, once=True),
                )
                search_input.on(
                    "update:model-value",
                    lambda: ui.timer(0.4, on_search_change, once=True),
                )

                ui.timer(0.1, load_modules, once=True)
                ui.timer(0.2, load_logs, once=True)
