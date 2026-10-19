"""allow timezone user intent

Revision ID: b8e2d4f16a93
Revises: f3a9c2e71b84
Create Date: 2026-10-19 12:30:00

"""
from typing import Sequence, Union

from alembic import op


revision: str = "b8e2d4f16a93"
down_revision: Union[str, Sequence[str], None] = "f3a9c2e71b84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_INTENTS_WITH_TIMEZONE = (
    "intent IN ('schedule', 'answer', 'study', 'unknown', 'add_words', 'timezone')"
)
_INTENTS_WITHOUT_TIMEZONE = (
    "intent IN ('schedule', 'answer', 'study', 'unknown', 'add_words')"
)


def upgrade() -> None:
    op.drop_constraint("ck_users_intent", "users", type_="check")
    op.create_check_constraint(
        "ck_users_intent",
        "users",
        _INTENTS_WITH_TIMEZONE,
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_intent", "users", type_="check")
    op.create_check_constraint(
        "ck_users_intent",
        "users",
        _INTENTS_WITHOUT_TIMEZONE,
    )
