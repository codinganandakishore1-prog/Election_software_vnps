"""WebSocket route registration (placeholder)."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.websocket.manager import manager


def register_websocket_routes(app: FastAPI) -> None:
    """Register WebSocket endpoints."""

    @app.websocket("/ws/live")
    async def live_results_socket(websocket: WebSocket) -> None:
        await manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    @app.websocket("/ws/dashboard")
    async def dashboard_socket(websocket: WebSocket) -> None:
        await manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)
