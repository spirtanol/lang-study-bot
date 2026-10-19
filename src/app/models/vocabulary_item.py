from sqlalchemy import ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel, IdMixin, TimestampMixin


class VocabularyItem(IdMixin, TimestampMixin, BaseModel):
    __tablename__ = "vocabulary_items"
    __table_args__ = (
        Index(
            "ix_vocabulary_items_user_id_points",
            "user_id",
            "points",
        ),
        Index(
            "uq_vocabulary_items_user_id_word_id",
            "user_id",
            "word_id",
            unique=True,
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    word_id: Mapped[int] = mapped_column(
        ForeignKey("words.id", ondelete="RESTRICT"),
        nullable=False,
    )
    points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
