"""Authentication integration tests."""

from fastapi.testclient import TestClient

from tests.conftest import TEST_ADMIN_PASSWORD, TEST_ADMIN_USERNAME


def test_login_returns_jwt(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": TEST_ADMIN_USERNAME, "password": TEST_ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["access_token"]
    assert payload["data"]["token_type"] == "bearer"


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": TEST_ADMIN_USERNAME, "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_protected_route_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/elections")
    assert response.status_code == 401


def test_protected_route_accepts_valid_token(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/elections", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert isinstance(payload["data"], list)


def test_current_user_profile(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["username"] == TEST_ADMIN_USERNAME


def test_update_current_user_profile(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.put(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"full_name": "Updated Admin", "email": "admin@example.com"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["full_name"] == "Updated Admin"
    assert payload["data"]["email"] == "admin@example.com"


def test_change_password_rejects_wrong_current(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.patch(
        "/api/v1/users/change-password",
        headers=auth_headers,
        json={"old_password": "wrong-password", "new_password": "NewPass@123"},
    )
    assert response.status_code in {400, 422}


def test_verify_token_endpoint(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post("/api/v1/auth/verify", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["valid"] is True
    assert payload["data"]["username"] == TEST_ADMIN_USERNAME
