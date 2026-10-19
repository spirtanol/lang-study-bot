"""add active session unique index

Revision ID: 72d4a9c1f8b3
Revises: 425f681a3637
Create Date: 2026-10-12 21:18:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "72d4a9c1f8b3"
down_revision: Union[str, Sequence[str], None] = "425f681a3637"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_study_sessions_active_user",
        "study_sessions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('pending', 'in_progress', 'deferred')"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_study_sessions_active_user",
        table_name="study_sessions",
    )
