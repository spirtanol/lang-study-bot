"""create telegram_updates table

Revision ID: d7f2a9c84e15
Revises: c4e8b1a27f90
Create Date: 2026-10-17 21:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7f2a9c84e15"
down_revision: Union[str, Sequence[str], None] = "c4e8b1a27f90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "telegram_updates",
        sa.Column("update_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("update_id"),
    )
    op.create_index(
        "ix_telegram_updates_created_at",
        "telegram_updates",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_telegram_updates_created_at",
        table_name="telegram_updates",
    )
    op.drop_table("telegram_updates")
