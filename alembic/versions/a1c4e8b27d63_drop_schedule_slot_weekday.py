"""drop schedule slot weekday

Revision ID: a1c4e8b27d63
Revises: 9f2c6e81a4b5
Create Date: 2026-10-16 11:55:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1c4e8b27d63"
down_revision: Union[str, Sequence[str], None] = "9f2c6e81a4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_WEEKDAY_VALUES = "weekday IN (1, 2, 3, 4, 5, 6, 7)"


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM study_schedule_slots AS slot
            USING study_schedule_slots AS kept
            WHERE slot.user_id = kept.user_id
              AND slot.local_time = kept.local_time
              AND slot.id > kept.id
            """
        )
    )
    op.drop_constraint(
        "ck_study_schedule_slots_weekday",
        "study_schedule_slots",
        type_="check",
    )
    op.drop_column("study_schedule_slots", "weekday")


def downgrade() -> None:
    op.add_column(
        "study_schedule_slots",
        sa.Column(
            "weekday",
            sa.SmallInteger(),
            nullable=False,
            server_default="1",
        ),
    )
    op.create_check_constraint(
        "ck_study_schedule_slots_weekday",
        "study_schedule_slots",
        _WEEKDAY_VALUES,
    )
    op.alter_column(
        "study_schedule_slots",
        "weekday",
        server_default=None,
    )
