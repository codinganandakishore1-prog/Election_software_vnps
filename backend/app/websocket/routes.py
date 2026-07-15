"""WebSocket route registration."""

from __future__ import annotations

import json

from election_platform.logging.setup import get_logger
from election_platform.schemas.websocket import WSChannel, WSMessageType
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, WebSocketException

from app.database.session import SessionLocal
from app.dependencies.container import get_container
from app.websocket.auth import authenticate_websocket
from app.websocket.manager import manager

logger = get_logger("backend.websocket")


async def _send_connected_message(websocket: WebSocket, channel: WSChannel) -> None:
    await manager.send_json(
        websocket,
        {
            "type": WSMessageType.CONNECTED.value,
            "channel": channel.value,
            "connected_clients": manager.connected_count_for(channel),
        },
    )


def register_websocket_routes(app: FastAPI) -> None:
    """Register WebSocket endpoints."""

    @app.websocket("/ws/live")
    async def live_results_socket(websocket: WebSocket) -> None:
        try:
            claims = authenticate_websocket(websocket, WSChannel.LIVE)
        except WebSocketException:
            await websocket.close(code=1008)
            return

        await manager.connect(
            websocket,
            channel=WSChannel.LIVE,
            user_id=claims.get("sub"),
            role=claims.get("role"),
        )
        await _send_connected_message(websocket, WSChannel.LIVE)

        db = SessionLocal()
        try:
            container = get_container(db)
            snapshot = container.analytics_service.get_live_results()
            await manager.send_json(
                websocket,
                {
                    "type": WSMessageType.LIVE_RESULTS_UPDATE.value,
                    "data": snapshot.model_dump(mode="json"),
                },
            )
        finally:
            db.close()

        try:
            while True:
                raw = await websocket.receive_text()
                await _handle_client_message(websocket, raw)
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            logger.info("Live WebSocket disconnected (remaining=%s)", manager.connected_count)
        except Exception:
            manager.disconnect(websocket)
            logger.exception("Live WebSocket error")

    @app.websocket("/ws/dashboard")
    async def dashboard_socket(websocket: WebSocket) -> None:
        try:
            claims = authenticate_websocket(websocket, WSChannel.DASHBOARD)
        except WebSocketException:
            await websocket.close(code=1008)
            return

        await manager.connect(
            websocket,
            channel=WSChannel.DASHBOARD,
            user_id=claims.get("sub"),
            role=claims.get("role"),
        )
        await _send_connected_message(websocket, WSChannel.DASHBOARD)

        db = SessionLocal()
        try:
            container = get_container(db)
            snapshot = container.analytics_service.get_dashboard_snapshot(
                connected_clients=manager.connected_count_for(WSChannel.DASHBOARD),
            )
            await manager.send_json(
                websocket,
                {
                    "type": WSMessageType.DASHBOARD_SNAPSHOT.value,
                    "data": snapshot.model_dump(mode="json"),
                },
            )
        finally:
            db.close()

        try:
            while True:
                raw = await websocket.receive_text()
                await _handle_client_message(websocket, raw)
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            logger.info("Dashboard WebSocket disconnected (remaining=%s)", manager.connected_count)
        except Exception:
            manager.disconnect(websocket)
            logger.exception("Dashboard WebSocket error")


async def _handle_client_message(websocket: WebSocket, raw: str) -> None:
    """Handle ping and snapshot refresh requests from clients."""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        await manager.send_json(
            websocket,
            {"type": WSMessageType.ERROR.value, "message": "Invalid JSON payload"},
        )
        return

    message_type = payload.get("type")
    if message_type == WSMessageType.PING.value:
        await manager.send_json(websocket, {"type": WSMessageType.PONG.value})
        return

    connection = manager.get_connection(websocket)
    if connection is None:
        return

    if message_type == "refresh":
        db = SessionLocal()
        try:
            container = get_container(db)
            if connection.channel == WSChannel.DASHBOARD:
                snapshot = container.analytics_service.get_dashboard_snapshot(
                    connected_clients=manager.connected_count_for(WSChannel.DASHBOARD),
                )
                await manager.send_json(
                    websocket,
                    {
                        "type": WSMessageType.DASHBOARD_SNAPSHOT.value,
                        "data": snapshot.model_dump(mode="json"),
                    },
                )
            else:
                snapshot = container.analytics_service.get_live_results()
                await manager.send_json(
                    websocket,
                    {
                        "type": WSMessageType.LIVE_RESULTS_UPDATE.value,
                        "data": snapshot.model_dump(mode="json"),
                    },
                )
        finally:
            db.close()
