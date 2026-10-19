from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import exists, func, literal, select, union_all, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import ColumnElement

from app.core.db import AsyncSession
from app.defs import FamiliarityLevel
from app.models import StudyAttempt, VocabularyItem, Word


@dataclass(frozen=True, slots=True)
class PickedItem:
    vocabulary_item_id: int
    word: str


class VocabularyItemRepository:
    def __init__(self, get_session: Callable[[], AsyncSession]):
        self._get_session = get_session

    async def add_points(self, item_id: int, delta: int) -> None:
        await self._get_session().execute(
            update(VocabularyItem)
            .where(VocabularyItem.id == item_id)
            .values(points=func.greatest(VocabularyItem.points + delta, 0))
        )

    async def exists_for_user(self, user_id: int) -> bool:
        statement = select(
            exists().where(
                VocabularyItem.user_id == user_id,
                VocabularyItem.points < FamiliarityLevel.GOOD,
            )
        )
        return bool(await self._get_session().scalar(statement))

    async def add(self, item: VocabularyItem) -> VocabularyItem | None:
        statement = (
            insert(VocabularyItem)
            .values(
                user_id=item.user_id,
                word_id=item.word_id,
                points=item.points,
            )
            .on_conflict_do_update(
                index_elements=[
                    VocabularyItem.user_id,
                    VocabularyItem.word_id,
                ],
                set_={"points": 0},
                where=VocabularyItem.points >= FamiliarityLevel.GOOD,
            )
            .returning(VocabularyItem)
        )
        return await self._get_session().scalar(statement)

    async def pick_for_session(
        self,
        user_id: int,
        session_id: int,
    ) -> PickedItem | None:
        weak_items = _candidate_ids(
            user_id,
            session_id,
            0,
            VocabularyItem.points < FamiliarityLevel.BAD,
        )
        learning_items = _candidate_ids(
            user_id,
            session_id,
            1,
            VocabularyItem.points >= FamiliarityLevel.BAD,
            VocabularyItem.points < FamiliarityLevel.GOOD,
        )
        picked = union_all(
            select(weak_items.c.id, weak_items.c.priority),
            select(learning_items.c.id, learning_items.c.priority),
        ).subquery()
        statement = (
            select(VocabularyItem.id, Word.text)
            .join(picked, VocabularyItem.id == picked.c.id)
            .join(Word, Word.id == VocabularyItem.word_id)
            .order_by(picked.c.priority)
            .limit(1)
        )
        row = (await self._get_session().execute(statement)).one_or_none()
        if row is None:
            return None
        vocabulary_item_id, word = row
        return PickedItem(vocabulary_item_id=vocabulary_item_id, word=word)


def _candidate_ids(
    user_id: int,
    session_id: int,
    priority: int,
    *criteria: ColumnElement[bool],
):
    not_asked = ~exists(
        select(StudyAttempt.id).where(
            StudyAttempt.session_id == session_id,
            StudyAttempt.vocabulary_item_id == VocabularyItem.id,
        )
    )
    return (
        select(
            VocabularyItem.id.label("id"),
            literal(priority).label("priority"),
        )
        .where(
            VocabularyItem.user_id == user_id,
            not_asked,
            *criteria,
        )
        .order_by(func.random())
        .limit(1)
        .subquery()
    )
