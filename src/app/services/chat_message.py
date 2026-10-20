from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from datetime import datetime, timedelta, timezone

from app.defs import MessageDirect
from app.models import ChatMessage
from app.repositories import ChatMessageRepository


class ChatMessageService:
    def __init__(
        self,
        messages: ChatMessageRepository,
        transaction: Callable[[], AbstractAsyncContextManager[None]],
        retention_days: int,
    ):
        self._messages = messages
        self._transaction = transaction
        self._retention_days = retention_days

    async def add(
        self,
        chat_id: int,
        direct: MessageDirect,
        message: str,
    ) -> ChatMessage:
        async with self._transaction():
            return await self._messages.add(chat_id, direct, message)

    async def delete_old(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self._retention_days)
        async with self._transaction():
            await self._messages.delete_older_than(cutoff)
