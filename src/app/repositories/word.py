from collections.abc import Callable

from sqlalchemy import func, not_, select, update
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

    async def append_translation(self, text: str, translation: str) -> None:
        addition = func.jsonb_build_array(translation)
        statement = (
            update(Word)
            .where(
                Word.text == text,
                not_(Word.translations.contains(addition)),
            )
            .values(translations=Word.translations.concat(addition))
        )
        await self._get_session().execute(statement)
