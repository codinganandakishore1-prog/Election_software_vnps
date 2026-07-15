"""WebSocket authentication helpers."""

from election_platform.schemas.websocket import WSChannel
from fastapi import WebSocket, WebSocketException, status

from app.security.jwt import JWTHandler


def _extract_token(websocket: WebSocket) -> str | None:
    token = websocket.query_params.get("token")
    if token:
        return token.strip()

    auth_header = websocket.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return None


def authenticate_websocket(websocket: WebSocket, channel: WSChannel) -> dict:
    """
    Validate JWT for WebSocket connections.

  - dashboard: requires admin access token
  - live: public (optional token accepted but not required)
    """
    if channel == WSChannel.LIVE:
        token = _extract_token(websocket)
        if not token:
            return {}
        payload = JWTHandler().decode_token_safe(token)
        return payload or {}

    token = _extract_token(websocket)
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")

    payload = JWTHandler().decode_token_safe(token)
    if payload is None or payload.get("type") != JWTHandler.TOKEN_TYPE_ACCESS:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token")

    return payload
