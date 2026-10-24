from collections.abc import Callable, Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select

from app.core.db import AsyncSession
from app.models import WordAddBatch


class WordAddBatchRepository:
    def __init__(self, get_session: Callable[[], AsyncSession]):
        self._get_session = get_session

    async def add(self, batch_id: UUID, word_ids: Sequence[int]) -> None:
        session = self._get_session()
        session.add_all(
            [
                WordAddBatch(batch_id=batch_id, word_id=word_id)
                for word_id in word_ids
            ]
        )
        await session.flush()

    async def word_ids(self, batch_id: UUID) -> list[int]:
        statement = select(WordAddBatch.word_id).where(
            WordAddBatch.batch_id == batch_id,
        )
        return list(await self._get_session().scalars(statement))

    async def delete_by_batch(self, batch_id: UUID) -> None:
        await self._get_session().execute(
            delete(WordAddBatch).where(WordAddBatch.batch_id == batch_id)
        )

    async def delete_older_than(self, cutoff: datetime) -> None:
        await self._get_session().execute(
            delete(WordAddBatch).where(WordAddBatch.created_at < cutoff)
        )
