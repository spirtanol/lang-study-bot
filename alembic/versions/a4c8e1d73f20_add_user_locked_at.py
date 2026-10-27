"""add user locked_at

Revision ID: a4c8e1d73f20
Revises: b7e4a2c91d58
Create Date: 2026-10-26 22:50:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4c8e1d73f20"
down_revision: Union[str, Sequence[str], None] = "b7e4a2c91d58"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "locked_at")
