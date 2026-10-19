"""allow add_words user intent

Revision ID: e5a9c3f18b26
Revises: d3b8f6a12c47
Create Date: 2026-10-15 15:56:00

"""
from typing import Sequence, Union

from alembic import op


revision: str = "e5a9c3f18b26"
down_revision: Union[str, Sequence[str], None] = "d3b8f6a12c47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_INTENTS_WITH_ADD_WORDS = (
    "intent IN ('schedule', 'answer', 'study', 'unknown', 'add_words')"
)
_INTENTS_WITHOUT_ADD_WORDS = (
    "intent IN ('schedule', 'answer', 'study', 'unknown')"
)


def upgrade() -> None:
    op.drop_constraint("ck_users_intent", "users", type_="check")
    op.create_check_constraint(
        "ck_users_intent",
        "users",
        _INTENTS_WITH_ADD_WORDS,
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_intent", "users", type_="check")
    op.create_check_constraint(
        "ck_users_intent",
        "users",
        _INTENTS_WITHOUT_ADD_WORDS,
    )
