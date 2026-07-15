"""WebSocket manager tests."""

import asyncio

from election_platform.schemas.websocket import WSChannel

from app.websocket.manager import ConnectionManager


class FakeWebSocket:
    def __init__(self) -> None:
        self.accepted = False
        self.sent: list[dict] = []
        self.closed = False

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)


def test_connect_and_broadcast_by_channel() -> None:
    async def run() -> None:
        manager = ConnectionManager()
        dashboard_socket = FakeWebSocket()
        live_socket = FakeWebSocket()

        await manager.connect(dashboard_socket, channel=WSChannel.DASHBOARD)
        await manager.connect(live_socket, channel=WSChannel.LIVE)

        assert manager.connected_count == 2
        assert manager.connected_count_for(WSChannel.DASHBOARD) == 1

        delivered = await manager.broadcast_to_channel(
            WSChannel.DASHBOARD,
            {"type": "dashboard_snapshot", "data": {"total_votes": 3}},
        )
        assert delivered == 1
        assert dashboard_socket.sent[0]["data"]["total_votes"] == 3
        assert live_socket.sent == []

        manager.disconnect(dashboard_socket)
        assert manager.connected_count == 1

    asyncio.run(run())


def test_broadcast_removes_dead_socket() -> None:
    async def run() -> None:
        manager = ConnectionManager()

        class FailingSocket(FakeWebSocket):
            async def send_json(self, message: dict) -> None:
                raise ConnectionError("socket closed")

        socket = FailingSocket()
        await manager.connect(socket, channel=WSChannel.DASHBOARD)
        delivered = await manager.broadcast_to_channel(WSChannel.DASHBOARD, {"type": "ping"})
        assert delivered == 0
        assert manager.connected_count == 0

    asyncio.run(run())
