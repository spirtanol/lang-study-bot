"""drop vocabulary item source

Revision ID: 9f2c6e81a4b5
Revises: e5a9c3f18b26
Create Date: 2026-10-15 19:40:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f2c6e81a4b5"
down_revision: Union[str, Sequence[str], None] = "e5a9c3f18b26"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SOURCE_VALUES = "source IN ('user', 'llm')"


def upgrade() -> None:
    op.drop_constraint(
        "ck_vocabulary_items_source",
        "vocabulary_items",
        type_="check",
    )
    op.drop_column("vocabulary_items", "source")


def downgrade() -> None:
    op.add_column(
        "vocabulary_items",
        sa.Column(
            "source",
            sa.String(length=8),
            nullable=False,
            server_default="user",
        ),
    )
    op.create_check_constraint(
        "ck_vocabulary_items_source",
        "vocabulary_items",
        _SOURCE_VALUES,
    )
    op.alter_column(
        "vocabulary_items",
        "source",
        server_default=None,
    )
