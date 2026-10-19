from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.db import AsyncSession
from app.models import Word


class WordRepository:
    def __init__(self, get_session: Callable[[], AsyncSession]):
        self._get_session = get_session

    async def get_by_text(self, text: str) -> Word | None:
        statement = select(Word).where(Word.text == text)
        return await self._get_session().scalar(statement)

    async def add(self, text: str, translations: list[str]) -> Word | None:
        statement = (
            insert(Word)
            .values(text=text, translations=translations)
            .on_conflict_do_nothing(index_elements=[Word.text])
            .returning(Word)
        )
        return await self._get_session().scalar(statement)
