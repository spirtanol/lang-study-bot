"""create chat_messages table

Revision ID: c9a4e7b15d28
Revises: b8e2d4f16a93
Create Date: 2026-10-20 12:50:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9a4e7b15d28"
down_revision: Union[str, Sequence[str], None] = "b8e2d4f16a93"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("direct", sa.String(length=3), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "direct IN ('in', 'out')",
            name="ck_chat_messages_direct",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chat_messages_chat_id_created_at",
        "chat_messages",
        ["chat_id", "created_at"],
    )
    op.create_index(
        "ix_chat_messages_created_at",
        "chat_messages",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_chat_messages_created_at",
        table_name="chat_messages",
    )
    op.drop_index(
        "ix_chat_messages_chat_id_created_at",
        table_name="chat_messages",
    )
    op.drop_table("chat_messages")
