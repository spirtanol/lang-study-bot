"""add user intent

Revision ID: f1a6c8d24e70
Revises: c5d9e2a71b48
Create Date: 2026-10-14 20:10:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a6c8d24e70"
down_revision: Union[str, Sequence[str], None] = "c5d9e2a71b48"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "intent",
            sa.String(length=16),
            server_default="unknown",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_users_intent",
        "users",
        "intent IN ('schedule', 'answer', 'study', 'unknown')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_intent", "users", type_="check")
    op.drop_column("users", "intent")
