"""add deferred_2 and rejected session statuses

Revision ID: c4e8b1a27f90
Revises: b6d1e9a43c82
Create Date: 2026-10-17 13:58:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e8b1a27f90"
down_revision: Union[str, Sequence[str], None] = "b6d1e9a43c82"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUSES = (
    "status IN ('completed', 'in_progress', 'pending', 'interrupted', "
    "'deferred', 'deferred_2', 'rejected', 'timed_out')"
)
_PREVIOUS_STATUSES = (
    "status IN ('completed', 'in_progress', 'pending', 'interrupted', "
    "'deferred', 'timed_out')"
)
_ACTIVE_WITH_DEFERRED_2 = (
    "status IN ('pending', 'in_progress', 'deferred', 'deferred_2')"
)
_ACTIVE_WITHOUT_DEFERRED_2 = (
    "status IN ('pending', 'in_progress', 'deferred')"
)


def upgrade() -> None:
    op.drop_constraint(
        "ck_study_sessions_status",
        "study_sessions",
        type_="check",
    )
    op.create_check_constraint(
        "ck_study_sessions_status",
        "study_sessions",
        _STATUSES,
    )
    op.drop_index(
        "uq_study_sessions_active_user",
        table_name="study_sessions",
    )
    op.create_index(
        "uq_study_sessions_active_user",
        "study_sessions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text(_ACTIVE_WITH_DEFERRED_2),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_study_sessions_active_user",
        table_name="study_sessions",
    )
    op.create_index(
        "uq_study_sessions_active_user",
        "study_sessions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text(_ACTIVE_WITHOUT_DEFERRED_2),
    )
    op.drop_constraint(
        "ck_study_sessions_status",
        "study_sessions",
        type_="check",
    )
    op.create_check_constraint(
        "ck_study_sessions_status",
        "study_sessions",
        _PREVIOUS_STATUSES,
    )
