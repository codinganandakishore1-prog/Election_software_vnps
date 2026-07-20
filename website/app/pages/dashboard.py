"""Dashboard page with live WebSocket updates."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from nicegui import app, ui

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.theme import apply_saved_theme, inject_theme
from app.websocket.client import WebSocketClient
from app.websocket.page_session import WebSocketPageSession, safe_ui_update


def _stat_color(color: str) -> str:
    mapping = {
        "primary": "text-primary",
        "positive": "text-positive",
        "warning": "text-warning",
        "info": "text-info",
        "negative": "text-negative",
    }
    return mapping.get(color, "text-primary")


def _format_last_vote(value: str | None) -> str:
    if not value:
        return "—"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%H:%M:%S")
    except ValueError:
        return value


def register_dashboard_routes() -> None:
    """Register the main dashboard route."""

    @ui.page("/dashboard")
    @require_auth
    async def dashboard_page() -> None:
        inject_theme()
        apply_saved_theme()

        state: dict[str, Any] = {
            "snapshot": None,
            "ws_connected": False,
        }
        ui_refs: dict[str, Any] = {}
        ws_client: WebSocketClient | None = None
        ws_session = WebSocketPageSession()

        def _update_ws_indicator() -> None:
            ws_badge = ui_refs.get("ws_status")
            if ws_badge is not None:
                if state["ws_connected"]:
                    ws_badge.set_text("Connected")
                    ws_badge.props("color=positive outline")
                else:
                    ws_badge.set_text("Reconnecting")
                    ws_badge.props("color=warning outline")

            system_items = ui_refs.get("system_items", {})
            if "websocket" in system_items:
                ws_item = system_items["websocket"]
                ws_item["value"].set_text("Connected" if state["ws_connected"] else "Reconnecting")
                ws_item["badge"].props(
                    f'color={"positive" if state["ws_connected"] else "warning"} outline'
                )

        def apply_snapshot(data: dict[str, Any]) -> None:
            state["snapshot"] = data
            election_name = data.get("election_name", "—")
            election_status = data.get("election_status", "—")
            total_votes = data.get("total_votes", 0)
            online_nodes = data.get("online_nodes", 0)
            total_nodes = data.get("total_nodes", 0)
            pending_queue = data.get("pending_queue", 0)
            sync_errors = data.get("sync_errors", 0)
            connected_clients = data.get("connected_clients", 0)
            last_vote = _format_last_vote(data.get("last_vote_time"))

            stat_values = {
                "election": election_name,
                "status": election_status,
                "votes": f"{total_votes:,}",
                "nodes": f"{online_nodes} / {total_nodes}",
                "queue": str(pending_queue),
                "last_vote": last_vote,
                "sync_errors": str(sync_errors),
                "connected": str(connected_clients),
            }
            for key, value in stat_values.items():
                label = ui_refs.get(f"stat_{key}")
                if label is not None:
                    label.set_text(value)

            _update_ws_indicator()

            node_table = ui_refs.get("node_table")
            if node_table is not None:
                rows = []
                for node in data.get("nodes", []):
                    status = node.get("status", "Unknown")
                    status_label = f"🟢 {status}" if status == "Online" else f"🔴 {status}"
                    rows.append(
                        {
                            "name": node.get("name", "—"),
                            "status": status_label,
                            "votes": str(node.get("votes", 0)),
                            "queue": str(node.get("queue", 0)),
                        }
                    )
                node_table.rows = rows
                node_table.update()

            activity_container = ui_refs.get("activity_container")
            if activity_container is not None:
                activity_container.clear()
                with activity_container:
                    for entry in data.get("activity", []):
                        with ui.element("div").classes("emp-activity-item"):
                            ui.label(entry.get("time", "")).classes("text-caption text-grey-6")
                            ui.label(entry.get("message", "")).classes("text-body2")

            chart_label = ui_refs.get("chart_summary")
            if chart_label is not None:
                points = data.get("votes_per_minute", [])
                if points:
                    total_recent = sum(point.get("count", 0) for point in points)
                    chart_label.set_text(f"{total_recent} votes in the last {len(points)} minutes")
                else:
                    chart_label.set_text("Waiting for vote activity…")

        def append_activity(message: str) -> None:
            activity_container = ui_refs.get("activity_container")
            if activity_container is None:
                return
            with activity_container:
                item = ui.element("div").classes("emp-activity-item")
                with item:
                    ui.label(datetime.now().strftime("%H:%M")).classes("text-caption text-grey-6")
                    ui.label(message).classes("text-body2")
            while len(activity_container.default_slot.children) > 8:
                activity_container.default_slot.children.pop(0)

        def on_ws_snapshot(payload: dict[str, Any]) -> None:
            data = payload.get("data")
            if isinstance(data, dict):
                apply_snapshot(data)

        def on_vote_synced(payload: dict[str, Any]) -> None:
            node_name = payload.get("node_name", "Node")
            count = payload.get("accepted_count", 0)
            append_activity(f"{count} vote(s) synced from {node_name}")
            if state.get("snapshot"):
                state["snapshot"]["total_votes"] = payload.get("total_votes", state["snapshot"].get("total_votes", 0))
                state["snapshot"]["last_vote_time"] = payload.get("last_vote_time")
                apply_snapshot(state["snapshot"])

        def on_heartbeat(payload: dict[str, Any]) -> None:
            snapshot = state.get("snapshot")
            if not isinstance(snapshot, dict):
                return
            nodes = snapshot.get("nodes", [])
            node_id = payload.get("node_id")
            for node in nodes:
                if node.get("node_id") == node_id:
                    node["status"] = payload.get("status", node.get("status"))
                    node["queue"] = payload.get("queue_size", node.get("queue", 0))
                    node["votes"] = payload.get("votes", node.get("votes", 0))
                    break
            else:
                nodes.append(
                    {
                        "node_id": node_id,
                        "name": payload.get("node_name", node_id),
                        "status": payload.get("status", "Online"),
                        "votes": payload.get("votes", 0),
                        "queue": payload.get("queue_size", 0),
                    }
                )
            snapshot["online_nodes"] = sum(1 for node in nodes if node.get("status") == "Online")
            apply_snapshot(snapshot)

        def on_sync_status(payload: dict[str, Any]) -> None:
            snapshot = state.get("snapshot")
            if not isinstance(snapshot, dict):
                return
            snapshot["pending_queue"] = payload.get("pending_queue", snapshot.get("pending_queue", 0))
            snapshot["sync_errors"] = payload.get("sync_errors", snapshot.get("sync_errors", 0))
            apply_snapshot(snapshot)

        def on_ws_status(payload: dict[str, Any]) -> None:
            if payload.get("channel") == "dashboard":
                state["ws_connected"] = bool(payload.get("connected"))
                _update_ws_indicator()
                snapshot = state.get("snapshot")
                if isinstance(snapshot, dict):
                    apply_snapshot(snapshot)

        async def load_initial() -> None:
            if AuthService.has_backend_token():
                data = await AnalyticsService.get_dashboard()
                if data and ws_session.active:
                    safe_ui_update(lambda: apply_snapshot(data))

        async def connect_websocket() -> None:
            nonlocal ws_client
            if not AuthService.has_backend_token():
                return
            ws_client = WebSocketClient(channel="dashboard")
            ws_client.on("dashboard_snapshot", ws_session.bind(on_ws_snapshot))
            ws_client.on("vote_counts", ws_session.bind(on_ws_snapshot))
            ws_client.on("vote_synced", ws_session.bind(on_vote_synced))
            ws_client.on("heartbeat_received", ws_session.bind(on_heartbeat))
            ws_client.on("node_status", ws_session.bind(on_heartbeat))
            ws_client.on("sync_status", ws_session.bind(on_sync_status))
            ws_session.subscribe("ws_status", on_ws_status)
            await ws_client.start(AuthService.get_access_token())

        with admin_shell("/dashboard") as content:
            with content:
                with ui.row().classes("items-center justify-between q-mb-lg w-full"):
                    with ui.column().classes("gap-0"):
                        ui.label("Dashboard").classes("emp-page-title")
                        subtitle = ui.label("Control center").classes("emp-page-subtitle")
                        ui_refs["subtitle"] = subtitle
                    ui_refs["ws_status"] = ui.badge("Connecting", color="grey").props("outline")

                stat_defs = [
                    ("election", "Election", "event", "primary", False),
                    ("status", "Status", "fiber_manual_record", "positive", True),
                    ("votes", "Votes Cast", "how_to_vote", "primary", False),
                    ("nodes", "Nodes Online", "devices", "positive", False),
                    ("queue", "Pending Queue", "pending_actions", "warning", False),
                    ("last_vote", "Last Vote", "schedule", "info", False),
                    ("sync_errors", "Sync Errors", "sync_problem", "negative", False),
                    ("connected", "Connected Users", "people", "primary", False),
                ]
                with ui.row().classes("w-full q-col-gutter-md"):
                    for key, label, icon, color, is_badge in stat_defs:
                        with ui.column().classes("col-12 col-sm-6 col-md-4 col-lg-3"):
                            with ui.element("div").classes("emp-stat-card h-full"):
                                with ui.row().classes("items-center justify-between q-mb-sm"):
                                    ui.label(label).classes("emp-stat-label")
                                    ui.icon(icon, size="sm").classes(_stat_color(color))
                                if is_badge:
                                    ui.html('<span class="emp-badge-live">LIVE</span>')
                                    ui_refs[f"stat_{key}"] = ui.label("—").classes("text-caption text-grey-7")
                                else:
                                    ui_refs[f"stat_{key}"] = ui.label("—").classes("emp-stat-value")

                with ui.row().classes("w-full q-col-gutter-md q-mt-md"):
                    with ui.column().classes("col-12 col-lg-8"):
                        with ui.element("div").classes("emp-card q-pa-md"):
                            with ui.row().classes("items-center justify-between q-mb-md"):
                                ui.label("Votes Per Minute").classes("text-weight-bold")
                                ui.badge("Live", color="positive").props("outline")
                            with ui.column().classes("items-center justify-center q-py-xl text-grey-6"):
                                ui.icon("show_chart", size="xl").classes("q-mb-sm opacity-50")
                                ui_refs["chart_summary"] = ui.label("Loading chart data…")
                    with ui.column().classes("col-12 col-lg-4"):
                        with ui.element("div").classes("emp-card q-pa-md"):
                            ui.label("System Status").classes("text-weight-bold q-mb-md")
                            ui_refs["system_items"] = {}
                            for item_key, item_label in [
                                ("website", "Website"),
                                ("database", "Database"),
                                ("websocket", "WebSocket"),
                            ]:
                                with ui.row().classes("items-center justify-between q-py-xs"):
                                    ui.label(item_label).classes("text-body2 text-grey-8")
                                    badge = ui.badge("—", color="grey").props("outline")
                                    ui_refs["system_items"][item_key] = {
                                        "value": badge,
                                        "badge": badge,
                                    }
                            ui_refs["system_items"]["website"]["value"].set_text("Online")
                            ui_refs["system_items"]["website"]["badge"].props("color=positive outline")
                            ui_refs["system_items"]["database"]["value"].set_text("Connected")
                            ui_refs["system_items"]["database"]["badge"].props("color=positive outline")

                with ui.row().classes("w-full q-col-gutter-md q-mt-md"):
                    with ui.column().classes("col-12 col-lg-7"):
                        columns = [
                            {"name": "name", "label": "Node", "field": "name", "align": "left"},
                            {"name": "status", "label": "Status", "field": "status", "align": "left"},
                            {"name": "votes", "label": "Votes", "field": "votes", "align": "right"},
                            {"name": "queue", "label": "Queue", "field": "queue", "align": "right"},
                        ]
                        with ui.element("div").classes("emp-card q-pa-md"):
                            ui.label("Node Health").classes("text-weight-bold q-mb-md")
                            ui_refs["node_table"] = (
                                ui.table(columns=columns, rows=[], row_key="name")
                                .props("flat dense")
                                .classes("w-full")
                            )
                    with ui.column().classes("col-12 col-lg-5"):
                        with ui.element("div").classes("emp-card q-pa-md"):
                            ui.label("Recent Activity").classes("text-weight-bold q-mb-md")
                            ui_refs["activity_container"] = ui.column().classes("w-full")

        await load_initial()
        await connect_websocket()

        async def cleanup() -> None:
            ws_session.deactivate()
            if ws_client is not None:
                await ws_client.stop()

        app.on_disconnect(cleanup)
