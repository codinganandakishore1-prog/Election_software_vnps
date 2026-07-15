"""soft deletes, candidate constraint, seed data

Revision ID: a1b2c3d4e5f6
Revises: 35e58f243b19
Create Date: 2026-07-13 18:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "35e58f243b19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLE_ROWS = (
    {
        "id": "00000000-0000-4000-8000-000000000001",
        "role_name": "Super Administrator",
        "description": "Full platform access including user deletion.",
    },
    {
        "id": "00000000-0000-4000-8000-000000000002",
        "role_name": "Administrator",
        "description": "Election and candidate management.",
    },
    {
        "id": "00000000-0000-4000-8000-000000000003",
        "role_name": "Viewer",
        "description": "Read-only access to elections, reports, and analytics.",
    },
)

HOUSE_ROWS = (
    {
        "id": "00000000-0000-4000-8000-000000000101",
        "house_name": "Pallava",
        "color": "#C0392B",
        "active": True,
    },
    {
        "id": "00000000-0000-4000-8000-000000000102",
        "house_name": "Pandya",
        "color": "#2980B9",
        "active": True,
    },
    {
        "id": "00000000-0000-4000-8000-000000000103",
        "house_name": "Chera",
        "color": "#27AE60",
        "active": True,
    },
    {
        "id": "00000000-0000-4000-8000-000000000104",
        "house_name": "Chola",
        "color": "#F39C12",
        "active": True,
    },
)


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column("reports", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("reports", "active", server_default=None)

    op.add_column(
        "notifications",
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "notifications",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("notifications", "active", server_default=None)

    op.add_column("themes", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "report_templates",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_check_constraint(
        "ck_candidates_display_order_min",
        "candidates",
        "display_order >= 1",
    )

    for row in ROLE_ROWS:
        op.execute(
            sa.text(
                "INSERT INTO roles (id, role_name, description) "
                "SELECT :id, :role_name, :description "
                "WHERE NOT EXISTS (SELECT 1 FROM roles WHERE id = :id)"
            ).bindparams(**row)
        )

    for row in HOUSE_ROWS:
        op.execute(
            sa.text(
                "INSERT INTO houses (id, house_name, color, active) "
                "SELECT :id, :house_name, :color, :active "
                "WHERE NOT EXISTS (SELECT 1 FROM houses WHERE id = :id)"
            ).bindparams(**row)
        )


def downgrade() -> None:
    for house_id in (row["id"] for row in reversed(HOUSE_ROWS)):
        op.execute(sa.text("DELETE FROM houses WHERE id = :id").bindparams(id=house_id))

    for role_id in (row["id"] for row in reversed(ROLE_ROWS)):
        op.execute(sa.text("DELETE FROM roles WHERE id = :id").bindparams(id=role_id))

    op.drop_constraint("ck_candidates_display_order_min", "candidates", type_="check")
    op.drop_column("report_templates", "deleted_at")
    op.drop_column("themes", "deleted_at")
    op.drop_column("notifications", "deleted_at")
    op.drop_column("notifications", "active")
    op.drop_column("reports", "deleted_at")
    op.drop_column("reports", "active")
