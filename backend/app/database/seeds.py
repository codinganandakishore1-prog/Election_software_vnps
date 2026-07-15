"""Default database seed data per SRS."""

import uuid

from election_platform.enums.roles import UserRole
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.house import House
from app.models.user import Role, User
from app.security.password import PasswordHasher

# Deterministic UUIDs keep seeds idempotent across environments.
ROLE_IDS = {
    UserRole.SUPER_ADMINISTRATOR: "00000000-0000-4000-8000-000000000001",
    UserRole.ADMINISTRATOR: "00000000-0000-4000-8000-000000000002",
    UserRole.VIEWER: "00000000-0000-4000-8000-000000000003",
}

DEFAULT_USER_SEEDS = (
    {
        "id": "00000000-0000-4000-8000-000000000901",
        "username": "admin",
        "password": "admin123",
        "role": UserRole.ADMINISTRATOR,
        "full_name": "Election Administrator",
    },
    {
        "id": "00000000-0000-4000-8000-000000000902",
        "username": "superadmin",
        "password": "super123",
        "role": UserRole.SUPER_ADMINISTRATOR,
        "full_name": "Super Administrator",
    },
    {
        "id": "00000000-0000-4000-8000-000000000903",
        "username": "viewer",
        "password": "viewer123",
        "role": UserRole.VIEWER,
        "full_name": "Results Viewer",
    },
)

HOUSE_SEEDS = (
    {"id": "00000000-0000-4000-8000-000000000101", "house_name": "Pallava", "color": "#C0392B"},
    {"id": "00000000-0000-4000-8000-000000000102", "house_name": "Pandya", "color": "#2980B9"},
    {"id": "00000000-0000-4000-8000-000000000103", "house_name": "Chera", "color": "#27AE60"},
    {"id": "00000000-0000-4000-8000-000000000104", "house_name": "Chola", "color": "#F39C12"},
)

ROLE_DESCRIPTIONS = {
    UserRole.SUPER_ADMINISTRATOR: "Full platform access including user deletion.",
    UserRole.ADMINISTRATOR: "Election and candidate management.",
    UserRole.VIEWER: "Read-only access to elections, reports, and analytics.",
}


def seed_roles(db: Session) -> int:
    """Insert default roles if missing. Returns number of rows created."""
    created = 0
    for role_enum, role_id in ROLE_IDS.items():
        exists = db.scalar(select(Role.id).where(Role.id == role_id))
        if exists:
            continue
        db.add(
            Role(
                id=role_id,
                role_name=role_enum.value,
                description=ROLE_DESCRIPTIONS[role_enum],
            )
        )
        created += 1
    return created


def seed_houses(db: Session) -> int:
    """Insert default school houses if missing. Returns number of rows created."""
    created = 0
    for house_data in HOUSE_SEEDS:
        exists = db.scalar(select(House.id).where(House.id == house_data["id"]))
        if exists:
            continue
        db.add(
            House(
                id=house_data["id"],
                house_name=house_data["house_name"],
                color=house_data["color"],
                active=True,
            )
        )
        created += 1
    return created


def seed_default_users(db: Session) -> int:
    """Insert demo administrator accounts if missing. Returns number created."""
    hasher = PasswordHasher()
    created = 0
    for user_data in DEFAULT_USER_SEEDS:
        exists = db.scalar(select(User.id).where(User.username == user_data["username"]))
        if exists:
            continue
        db.add(
            User(
                id=user_data["id"],
                username=user_data["username"],
                password_hash=hasher.hash_password(user_data["password"]),
                role_id=ROLE_IDS[user_data["role"]],
                full_name=user_data["full_name"],
                active=True,
            )
        )
        created += 1
    return created


def seed_database(db: Session) -> dict[str, int]:
    """Seed all required master data. Safe to call multiple times."""
    from app.dependencies.container import get_container

    container = get_container(db)
    theme_created = container.theme_service.seed_default_theme()

    results = {
        "roles": seed_roles(db),
        "houses": seed_houses(db),
        "themes": 1 if theme_created else 0,
        "users": seed_default_users(db),
    }
    db.flush()
    return results


def new_uuid() -> str:
    """Generate a new UUID string for application use."""
    return str(uuid.uuid4())
