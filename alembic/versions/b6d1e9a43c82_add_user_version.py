"""add user version

Revision ID: b6d1e9a43c82
Revises: a1c4e8b27d63
Create Date: 2026-10-16 14:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b6d1e9a43c82"
down_revision: Union[str, Sequence[str], None] = "a1c4e8b27d63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "version",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
    )
    op.create_index(
        "ix_users_telegram_user_id_version",
        "users",
        ["telegram_user_id", "version"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_users_telegram_user_id_version",
        table_name="users",
    )
    op.drop_column("users", "version")
