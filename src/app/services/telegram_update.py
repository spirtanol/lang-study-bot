from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from datetime import datetime, timezone

from app.defs import TELEGRAM_UPDATE_TTL
from app.repositories import TelegramUpdateAlreadyExistsError, TelegramUpdateRepository


class TelegramUpdateService:
    def __init__(
        self,
        updates: TelegramUpdateRepository,
        transaction: Callable[[], AbstractAsyncContextManager[None]],
    ):
        self._updates = updates
        self._transaction = transaction

    async def add_update(self, update_id: int) -> bool:
        try:
            async with self._transaction():
                await self._updates.add(update_id)
        except TelegramUpdateAlreadyExistsError:
            return False
        return True

    async def delete_old(self) -> None:
        cutoff = datetime.now(timezone.utc) - TELEGRAM_UPDATE_TTL
        async with self._transaction():
            await self._updates.delete_older_than(cutoff)
