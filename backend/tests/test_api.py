"""API endpoint smoke tests."""

from fastapi.testclient import TestClient


def test_health_database_endpoint(client: TestClient) -> None:
    response = client.get("/health/database")
    assert response.status_code == 200
    assert response.json()["data"]["connected"] is True


def test_websocket_health_endpoint(client: TestClient) -> None:
    response = client.get("/health/websocket")
    assert response.status_code == 200
    assert "connected_clients" in response.json()["data"]
