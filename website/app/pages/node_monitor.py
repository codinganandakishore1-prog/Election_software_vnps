"""Node monitor page with live WebSocket status updates."""

from __future__ import annotations

from typing import Any

from nicegui import app, ui

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.dependencies.container import get_website_container
from app.services.auth_service import AuthService
from app.theme import apply_saved_theme, inject_theme
from app.websocket.client import WebSocketClient
from app.websocket.page_session import WebSocketPageSession, safe_ui_update


def register_node_monitor_routes() -> None:
    """Register the node monitoring page."""

    @ui.page("/nodes")
    @require_auth
    async def node_monitor_page() -> None:
        inject_theme()
        apply_saved_theme()

        state: dict[str, Any] = {"nodes": [], "ws_connected": False}
        ui_refs: dict[str, Any] = {}
        ws_client: WebSocketClient | None = None
        ws_session = WebSocketPageSession()

        def apply_nodes(nodes: list[dict[str, Any]]) -> None:
            state["nodes"] = nodes
            table = ui_refs.get("node_table")
            if table is None:
                return
            rows = []
            for node in nodes:
                status = node.get("status", "Unknown")
                status_label = f"🟢 {status}" if status == "Online" else f"🔴 {status}"
                rows.append(
                    {
                        "name": node.get("node_name") or node.get("name", "—"),
                        "type": node.get("election_type", "—"),
                        "status": status_label,
                        "queue": str(node.get("queue_size", node.get("queue", 0))),
                        "sync": node.get("sync_status", "—") or "—",
                        "votes": str(node.get("votes", "—")),
                    }
                )
            table.rows = rows
            table.update()

            online = sum(1 for node in nodes if node.get("status") == "Online")
            summary = ui_refs.get("summary")
            if summary is not None:
                summary.set_text(f"{online} / {len(nodes)} nodes online")

        def update_node_from_ws(payload: dict[str, Any]) -> None:
            node_id = payload.get("node_id")
            nodes = list(state.get("nodes", []))
            for node in nodes:
                key = node.get("id") or node.get("node_id")
                if key == node_id:
                    node["status"] = payload.get("status", node.get("status"))
                    node["queue_size"] = payload.get("queue_size", node.get("queue_size", 0))
                    node["sync_status"] = payload.get("sync_status", node.get("sync_status"))
                    if "votes" in payload:
                        node["votes"] = payload["votes"]
                    break
            else:
                nodes.append(
                    {
                        "id": node_id,
                        "node_name": payload.get("node_name", node_id),
                        "election_type": "—",
                        "status": payload.get("status", "Online"),
                        "queue_size": payload.get("queue_size", 0),
                        "sync_status": payload.get("sync_status"),
                        "votes": payload.get("votes", 0),
                    }
                )
            apply_nodes(nodes)

        def on_dashboard_snapshot(payload: dict[str, Any]) -> None:
            data = payload.get("data")
            if isinstance(data, dict) and isinstance(data.get("nodes"), list):
                mapped = [
                    {
                        "id": node.get("node_id"),
                        "node_name": node.get("name"),
                        "status": node.get("status"),
                        "queue_size": node.get("queue"),
                        "sync_status": node.get("sync_status"),
                        "votes": node.get("votes"),
                        "election_type": "—",
                    }
                    for node in data["nodes"]
                ]
                apply_nodes(mapped)

        async def load_nodes() -> None:
            if not AuthService.has_backend_token():
                return
            client = get_website_container().api_client
            token = AuthService.get_access_token()
            response = await client.get("/nodes", headers={"Authorization": f"Bearer {token}"})
            success, _, data = client.parse_response(response)
            if success and isinstance(data, list) and ws_session.active:
                safe_ui_update(lambda: apply_nodes(data))

        async def connect_websocket() -> None:
            nonlocal ws_client
            if not AuthService.has_backend_token():
                return
            ws_client = WebSocketClient(channel="dashboard")
            ws_client.on("dashboard_snapshot", ws_session.bind(on_dashboard_snapshot))
            ws_client.on("heartbeat_received", ws_session.bind(update_node_from_ws))
            ws_client.on("node_status", ws_session.bind(update_node_from_ws))
            await ws_client.start(AuthService.get_access_token())

        with admin_shell("/nodes") as content:
            with content:
                with ui.row().classes("items-center justify-between q-mb-lg w-full"):
                    with ui.column().classes("gap-0"):
                        ui.label("Node Monitor").classes("emp-page-title")
                        ui.label("Real-time monitoring of all voting nodes.").classes("emp-page-subtitle")
                    ui_refs["summary"] = ui.badge("Loading", color="grey").props("outline")

                if not AuthService.has_backend_token():
                    ui.label(
                        "Connect to the backend API to monitor nodes in real time."
                    ).classes("text-warning text-caption q-mb-md")

                columns = [
                    {"name": "name", "label": "Node", "field": "name", "align": "left"},
                    {"name": "type", "label": "Type", "field": "type", "align": "left"},
                    {"name": "status", "label": "Status", "field": "status", "align": "left"},
                    {"name": "votes", "label": "Votes", "field": "votes", "align": "right"},
                    {"name": "queue", "label": "Queue", "field": "queue", "align": "right"},
                    {"name": "sync", "label": "Sync", "field": "sync", "align": "left"},
                ]
                with ui.element("div").classes("emp-card q-pa-md w-full"):
                    ui_refs["node_table"] = (
                        ui.table(columns=columns, rows=[], row_key="name")
                        .props("flat dense")
                        .classes("w-full")
                    )

        await load_nodes()
        await connect_websocket()

        async def cleanup() -> None:
            ws_session.deactivate()
            if ws_client is not None:
                await ws_client.stop()

        app.on_disconnect(cleanup)
