"""alter_vocabulary_items_indexes

Revision ID: 0b8705ccfa26
Revises: a8c3e1f04b92
Create Date: 2026-10-13 09:36:30.178729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b8705ccfa26'
down_revision: Union[str, Sequence[str], None] = 'a8c3e1f04b92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(
        op.f("ix_vocabulary_items_user_id"),
        table_name="vocabulary_items",
    )
    op.create_index(
        "ix_vocabulary_items_user_id_points",
        "vocabulary_items",
        ["user_id", "points"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_vocabulary_items_user_id_points",
        table_name="vocabulary_items",
    )
    op.create_index(
        op.f("ix_vocabulary_items_user_id"),
        "vocabulary_items",
        ["user_id"],
        unique=False,
    )
