"""extend themes for branding management

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-13 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("themes", sa.Column("school_name", sa.String(length=255), nullable=True))
    op.add_column("themes", sa.Column("school_logo_path", sa.String(length=255), nullable=True))
    op.add_column("themes", sa.Column("election_logo_path", sa.String(length=255), nullable=True))
    op.add_column("themes", sa.Column("background_light_path", sa.String(length=255), nullable=True))
    op.add_column("themes", sa.Column("background_dark_path", sa.String(length=255), nullable=True))
    op.add_column("themes", sa.Column("background_welcome_path", sa.String(length=255), nullable=True))
    op.add_column("themes", sa.Column("font_heading", sa.String(length=100), nullable=True))
    op.add_column("themes", sa.Column("font_body", sa.String(length=100), nullable=True))
    op.add_column("themes", sa.Column("font_accent", sa.String(length=100), nullable=True))
    op.add_column("themes", sa.Column("warning_color", sa.String(length=20), nullable=True))
    op.add_column("themes", sa.Column("danger_color", sa.String(length=20), nullable=True))
    op.add_column("themes", sa.Column("background_color", sa.String(length=20), nullable=True))
    op.add_column("themes", sa.Column("surface_color", sa.String(length=20), nullable=True))
    op.add_column("themes", sa.Column("text_primary_color", sa.String(length=20), nullable=True))
    op.add_column("themes", sa.Column("text_secondary_color", sa.String(length=20), nullable=True))
    op.add_column("themes", sa.Column("icon_app_path", sa.String(length=255), nullable=True))
    op.add_column("themes", sa.Column("icon_favicon_path", sa.String(length=255), nullable=True))
    op.add_column(
        "themes",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.add_column(
        "themes",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("themes", "updated_at")
    op.drop_column("themes", "created_at")
    op.drop_column("themes", "icon_favicon_path")
    op.drop_column("themes", "icon_app_path")
    op.drop_column("themes", "text_secondary_color")
    op.drop_column("themes", "text_primary_color")
    op.drop_column("themes", "surface_color")
    op.drop_column("themes", "background_color")
    op.drop_column("themes", "danger_color")
    op.drop_column("themes", "warning_color")
    op.drop_column("themes", "font_accent")
    op.drop_column("themes", "font_body")
    op.drop_column("themes", "font_heading")
    op.drop_column("themes", "background_welcome_path")
    op.drop_column("themes", "background_dark_path")
    op.drop_column("themes", "background_light_path")
    op.drop_column("themes", "election_logo_path")
    op.drop_column("themes", "school_logo_path")
    op.drop_column("themes", "school_name")
