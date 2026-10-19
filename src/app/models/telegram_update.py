from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class TelegramUpdate(BaseModel):
    __tablename__ = "telegram_updates"
    __table_args__ = (
        Index("ix_telegram_updates_created_at", "created_at"),
    )

    update_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
