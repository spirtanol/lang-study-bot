"""create word_add_batches table

Revision ID: b7e4a2c91d58
Revises: c9a4e7b15d28
Create Date: 2026-10-23 19:10:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "b7e4a2c91d58"
down_revision: Union[str, Sequence[str], None] = "c9a4e7b15d28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "word_add_batches",
        sa.Column("batch_id", UUID(as_uuid=True), nullable=False),
        sa.Column("word_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["word_id"],
            ["words.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("batch_id", "word_id"),
    )
    op.create_index(
        "ix_word_add_batches_created_at",
        "word_add_batches",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_word_add_batches_created_at",
        table_name="word_add_batches",
    )
    op.drop_table("word_add_batches")
