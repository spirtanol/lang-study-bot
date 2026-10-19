"""add skipped study attempt status

Revision ID: f3a9c2e71b84
Revises: d7f2a9c84e15
Create Date: 2026-10-18 22:30:00

"""
from typing import Sequence, Union

from alembic import op


revision: str = "f3a9c2e71b84"
down_revision: Union[str, Sequence[str], None] = "d7f2a9c84e15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUSES = (
    "status IN ('correct', 'incorrect', 'pending', 'timed_out', 'skipped')"
)
_PREVIOUS_STATUSES = (
    "status IN ('correct', 'incorrect', 'pending', 'timed_out')"
)


def upgrade() -> None:
    op.drop_constraint(
        "ck_study_attempts_status",
        "study_attempts",
        type_="check",
    )
    op.create_check_constraint(
        "ck_study_attempts_status",
        "study_attempts",
        _STATUSES,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_study_attempts_status",
        "study_attempts",
        type_="check",
    )
    op.create_check_constraint(
        "ck_study_attempts_status",
        "study_attempts",
        _PREVIOUS_STATUSES,
    )
