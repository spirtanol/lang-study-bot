"""add shared words catalog

Revision ID: d3b8f6a12c47
Revises: f1a6c8d24e70
Create Date: 2026-10-15 13:48:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "d3b8f6a12c47"
down_revision: Union[str, Sequence[str], None] = "f1a6c8d24e70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TRANSLATIONS_ARE_STRINGS = """
CASE
    WHEN jsonb_typeof(translations) <> 'array' THEN FALSE
    ELSE NOT jsonb_path_exists(
        translations,
        '$[*] ? (@.type() != "string")'
    )
END
"""


def upgrade() -> None:
    op.create_table(
        "words",
        sa.Column("text", sa.String(length=256), nullable=False),
        sa.Column(
            "translations",
            JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
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
            "text = lower(text)",
            name="ck_words_text_lowercase",
        ),
        sa.CheckConstraint(
            _TRANSLATIONS_ARE_STRINGS,
            name="ck_words_translations_array",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("uq_words_text", "words", ["text"], unique=True)
    op.execute(
        sa.text(
            """
            INSERT INTO words (text, translations, created_at, updated_at)
            SELECT DISTINCT lower(text), '[]'::jsonb, now(), now()
            FROM vocabulary_items
            """
        )
    )
    op.add_column(
        "vocabulary_items",
        sa.Column("word_id", sa.Integer(), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE vocabulary_items
            SET word_id = words.id
            FROM words
            WHERE words.text = lower(vocabulary_items.text)
            """
        )
    )
    op.alter_column(
        "vocabulary_items",
        "word_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_vocabulary_items_word_id",
        "vocabulary_items",
        "words",
        ["word_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "uq_vocabulary_items_user_id_word_id",
        "vocabulary_items",
        ["user_id", "word_id"],
        unique=True,
    )
    op.drop_column("vocabulary_items", "text")


def downgrade() -> None:
    op.add_column(
        "vocabulary_items",
        sa.Column("text", sa.String(length=256), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE vocabulary_items
            SET text = words.text
            FROM words
            WHERE words.id = vocabulary_items.word_id
            """
        )
    )
    op.alter_column(
        "vocabulary_items",
        "text",
        existing_type=sa.String(length=256),
        nullable=False,
    )
    op.drop_index(
        "uq_vocabulary_items_user_id_word_id",
        table_name="vocabulary_items",
    )
    op.drop_constraint(
        "fk_vocabulary_items_word_id",
        "vocabulary_items",
        type_="foreignkey",
    )
    op.drop_column("vocabulary_items", "word_id")
    op.drop_index("uq_words_text", table_name="words")
    op.drop_table("words")
