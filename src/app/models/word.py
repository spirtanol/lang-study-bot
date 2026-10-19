from sqlalchemy import CheckConstraint, Index, String, text as sql_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel, IdMixin, TimestampMixin


class Word(IdMixin, TimestampMixin, BaseModel):
    __tablename__ = "words"
    __table_args__ = (
        CheckConstraint(
            "text = lower(text)",
            name="ck_words_text_lowercase",
        ),
        CheckConstraint(
            """
            CASE
                WHEN jsonb_typeof(translations) <> 'array' THEN FALSE
                ELSE NOT jsonb_path_exists(
                    translations,
                    '$[*] ? (@.type() != "string")'
                )
            END
            """,
            name="ck_words_translations_array",
        ),
        Index("uq_words_text", "text", unique=True),
    )

    text: Mapped[str] = mapped_column(String(256), nullable=False)
    translations: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=sql_text("'[]'::jsonb"),
    )
