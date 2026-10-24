from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class WordAddBatch(BaseModel):
    __tablename__ = "word_add_batches"
    __table_args__ = (
        Index("ix_word_add_batches_created_at", "created_at"),
    )

    batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
    )
    word_id: Mapped[int] = mapped_column(
        ForeignKey("words.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
