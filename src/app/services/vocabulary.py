from collections.abc import Callable, Sequence
from contextlib import AbstractAsyncContextManager

from app.models import VocabularyItem, Word
from app.repositories import VocabularyItemRepository

from .word import WordService


class VocabularyService:
    def __init__(
        self,
        repository: VocabularyItemRepository,
        words: WordService,
        transaction: Callable[[], AbstractAsyncContextManager[None]],
    ):
        self._repository = repository
        self._words = words
        self._transaction = transaction

    async def has_items(self, user_id: int) -> bool:
        async with self._transaction():
            return await self._repository.exists_for_user(user_id)

    async def add_items(self, user_id: int, texts: Sequence[str]) -> list[Word]:
        return [await self.add_item(user_id, text) for text in texts]

    async def add_by_ids(self, user_id: int, word_ids: Sequence[int]) -> None:
        async with self._transaction():
            for word_id in word_ids:
                await self._repository.add(
                    VocabularyItem(
                        user_id=user_id,
                        word_id=word_id,
                        points=0,
                    )
                )

    async def add_item(self, user_id: int, text: str) -> Word:
        word = await self._words.get_or_create(text)
        async with self._transaction():
            await self._repository.add(
                VocabularyItem(
                    user_id=user_id,
                    word_id=word.id,
                    points=0,
                )
            )
        return word
