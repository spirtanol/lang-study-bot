import unicodedata
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from app.graphs import AddWordsGraph
from app.models import Word
from app.repositories import WordRepository

from .exceptions import WordNotAdded

WORD_TEXT_MAX_LENGTH = 256
_TOO_LONG_REASON = "слишком длинное"


def _clean_single_word(text: str) -> str:
    if len(text.split()) != 1:
        return text
    start = 0
    end = len(text)
    while start < end and unicodedata.category(text[start]).startswith("P"):
        start += 1
    while end > start and unicodedata.category(text[end - 1]).startswith("P"):
        end -= 1
    return text[start:end]


class WordService:
    def __init__(
        self,
        repository: WordRepository,
        add_words: AddWordsGraph,
        transaction: Callable[[], AbstractAsyncContextManager[None]],
    ):
        self._repository = repository
        self._add_words = add_words
        self._transaction = transaction

    async def get_or_create(self, text: str) -> Word:
        word_text = _clean_single_word(text.strip().lower())
        if not word_text or len(word_text) > WORD_TEXT_MAX_LENGTH:
            raise WordNotAdded(_TOO_LONG_REASON)

        async with self._transaction():
            existing = await self._repository.get_by_text(word_text)
            if existing is not None:
                return existing

        verdict = await self._add_words.run(word_text)
        if not verdict.accept:
            raise WordNotAdded(verdict.reason)

        async with self._transaction():
            created = await self._repository.add(
                word_text,
                list(verdict.translations),
            )
            if created is not None:
                return created

            existing = await self._repository.get_by_text(word_text)
            if existing is None:
                raise RuntimeError("Слово не сохранилось и не найдено")
            return existing
