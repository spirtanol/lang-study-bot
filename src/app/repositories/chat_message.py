from collections.abc import Callable
from datetime import datetime

from sqlalchemy import delete

from app.core.db import AsyncSession
from app.defs import MessageDirect
from app.models import ChatMessage


class ChatMessageRepository:
    def __init__(self, get_session: Callable[[], AsyncSession]):
        self._get_session = get_session

    async def add(
        self,
        chat_id: int,
        direct: MessageDirect,
        message: str,
    ) -> ChatMessage:
        row = ChatMessage(chat_id=chat_id, direct=direct, message=message)
        session = self._get_session()
        session.add(row)
        await session.flush()
        return row

    async def delete_older_than(self, cutoff: datetime) -> None:
        await self._get_session().execute(
            delete(ChatMessage).where(ChatMessage.created_at < cutoff)
        )
