"""API integration tests."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health_reports_database_status(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "database_connected" in payload["data"]


def test_settings_read_and_update(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/settings", headers=auth_headers)
    assert response.status_code == 200

    update = client.put(
        "/api/v1/settings",
        headers=auth_headers,
        json={
            "school_name": "VNPS Test School",
            "timezone": "Asia/Kolkata",
            "maintenance_mode": False,
        },
    )
    assert update.status_code == 200
    payload = update.json()
    assert payload["success"] is True
    assert payload["data"]["school_name"] == "VNPS Test School"


def test_database_settings_masked_password(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/settings/database", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert "password" not in payload["data"]
    assert payload["data"]["password_configured"] is False


def test_candidates_list_empty(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/candidates", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"] == []


def test_reports_list_empty(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/reports", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert isinstance(payload["data"], list)
