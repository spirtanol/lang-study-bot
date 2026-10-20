from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum as SAEnum, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.defs import MessageDirect

from .base import BaseModel, IdMixin, enum_check_constraint


class ChatMessage(IdMixin, BaseModel):
    __tablename__ = "chat_messages"
    __table_args__ = (
        enum_check_constraint(
            "direct",
            MessageDirect,
            "ck_chat_messages_direct",
        ),
        Index(
            "ix_chat_messages_chat_id_created_at",
            "chat_id",
            "created_at",
        ),
        Index("ix_chat_messages_created_at", "created_at"),
    )

    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    direct: Mapped[MessageDirect] = mapped_column(
        SAEnum(
            MessageDirect,
            name="ck_chat_messages_direct",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda items: [item.value for item in items],
            length=3,
        ),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
