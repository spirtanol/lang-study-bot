"""add study schedule slots and user next run

Revision ID: c5d9e2a71b48
Revises: 0b8705ccfa26
Create Date: 2026-10-14 16:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c5d9e2a71b48"
down_revision: Union[str, Sequence[str], None] = "0b8705ccfa26"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_users_next_run_at",
        "users",
        ["next_run_at"],
        postgresql_where=sa.text("next_run_at IS NOT NULL"),
    )
    op.create_table(
        "study_schedule_slots",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("local_time", sa.Time(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "weekday IN (1, 2, 3, 4, 5, 6, 7)",
            name="ck_study_schedule_slots_weekday",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.telegram_user_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("study_schedule_slots")
    op.drop_index("ix_users_next_run_at", table_name="users")
    op.drop_column("users", "next_run_at")
