from collections.abc import Callable, Sequence
from contextlib import AbstractAsyncContextManager
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.repositories import WordAddBatchRepository


class WordAddBatchService:
    def __init__(
        self,
        repository: WordAddBatchRepository,
        transaction: Callable[[], AbstractAsyncContextManager[None]],
        retention_hours: int,
    ):
        self._repository = repository
        self._transaction = transaction
        self._retention_hours = retention_hours

    async def add(self, word_ids: Sequence[int]) -> UUID:
        batch_id = uuid4()
        unique_ids = list(dict.fromkeys(word_ids))
        async with self._transaction():
            await self._repository.add(batch_id, unique_ids)
        return batch_id

    async def word_ids(self, batch_id: UUID) -> list[int]:
        async with self._transaction():
            return await self._repository.word_ids(batch_id)

    async def remove_batch(self, batch_id: UUID) -> None:
        async with self._transaction():
            await self._repository.delete_by_batch(batch_id)

    async def delete_old(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self._retention_hours)
        async with self._transaction():
            await self._repository.delete_older_than(cutoff)
