"""add study attempt unique constraint

Revision ID: a8c3e1f04b92
Revises: 72d4a9c1f8b3
Create Date: 2026-10-13 13:12:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a8c3e1f04b92"
down_revision: Union[str, Sequence[str], None] = "72d4a9c1f8b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(
        op.f("ix_study_attempts_session_id"),
        table_name="study_attempts",
    )
    op.drop_index(
        op.f("ix_study_attempts_vocabulary_item_id"),
        table_name="study_attempts",
    )
    op.create_index(
        op.f("uq_study_attempts_session_vocabulary_item"),
        "study_attempts",
        ["session_id", "vocabulary_item_id"],
        unique=True,
    )
    op.create_index(
        "uq_study_attempts_pending_session",
        "study_attempts",
        ["session_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_study_attempts_pending_session",
        table_name="study_attempts",
    )
    op.drop_index(
        op.f("uq_study_attempts_session_vocabulary_item"),
        table_name="study_attempts",
    )
    op.create_index(
        op.f("ix_study_attempts_vocabulary_item_id"),
        "study_attempts",
        ["vocabulary_item_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_study_attempts_session_id"),
        "study_attempts",
        ["session_id"],
        unique=False,
    )
