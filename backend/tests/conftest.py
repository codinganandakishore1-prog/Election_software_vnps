"""Shared pytest fixtures for backend integration tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from election_platform.enums.roles import UserRole
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.seeds import ROLE_IDS, seed_database
from app.database.session import get_db
from app.main import create_app
from app.models.user import User
from app.security.password import PasswordHasher

import app.models  # noqa: F401 — register ORM metadata


TEST_ADMIN_ID = "00000000-0000-4000-8000-000000000901"
TEST_ADMIN_USERNAME = "admin"
TEST_ADMIN_PASSWORD = "admin123"


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide an isolated in-memory database session."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = session_factory()

    seed_database(session)
    session.add(
        User(
            id=TEST_ADMIN_ID,
            username=TEST_ADMIN_USERNAME,
            password_hash=PasswordHasher().hash_password(TEST_ADMIN_PASSWORD),
            role_id=ROLE_IDS[UserRole.ADMINISTRATOR],
            full_name="Test Administrator",
            active=True,
        )
    )
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI test client with database dependency override."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    """Authenticate and return bearer headers."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": TEST_ADMIN_USERNAME, "password": TEST_ADMIN_PASSWORD},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    token = payload["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
