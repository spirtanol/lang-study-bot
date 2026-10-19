from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert

from app.core.db import AsyncSession
from app.defs import StudyAttemptStatus
from app.models import StudyAttempt, StudySession, VocabularyItem, Word

from .exceptions import StudyAttemptAlreadyExistsError

ANSWERED_STATUSES = (
    StudyAttemptStatus.CORRECT,
    StudyAttemptStatus.INCORRECT,
    StudyAttemptStatus.SKIPPED
)


@dataclass(frozen=True, slots=True)
class AttemptCounts:
    correct: int
    incorrect: int
    skipped: int


@dataclass(frozen=True, slots=True)
class PendingQuestion:
    attempt_id: int
    session_id: int
    vocabulary_item_id: int
    word: str
    question_text: str
    translations: tuple[str, ...]
    updated_at: datetime


class StudyAttemptRepository:
    def __init__(self, get_session: Callable[[], AsyncSession]):
        self._get_session = get_session

    async def get_latest(self, session_id: int) -> StudyAttempt | None:
        statement = (
            select(StudyAttempt)
            .where(StudyAttempt.session_id == session_id)
            .order_by(StudyAttempt.updated_at.desc(), StudyAttempt.id.desc())
            .limit(1)
        )
        return await self._get_session().scalar(statement)

    async def get_pending(self, session_id: int) -> PendingQuestion | None:
        statement = (
            select(
                StudyAttempt.id,
                StudyAttempt.session_id,
                StudyAttempt.vocabulary_item_id,
                Word.text,
                StudyAttempt.question_text,
                Word.translations,
                StudySession.updated_at,
            )
            .join(
                VocabularyItem,
                VocabularyItem.id == StudyAttempt.vocabulary_item_id,
            )
            .join(Word, Word.id == VocabularyItem.word_id)
            .join(StudySession, StudySession.id == StudyAttempt.session_id)
            .where(
                StudyAttempt.session_id == session_id,
                StudyAttempt.status == StudyAttemptStatus.PENDING,
            )
            .limit(1)
        )
        row = (await self._get_session().execute(statement)).one_or_none()
        if row is None:
            return None
        (
            attempt_id,
            attempt_session_id,
            vocabulary_item_id,
            word,
            question_text,
            translations,
            updated_at,
        ) = row
        return PendingQuestion(
            attempt_id=attempt_id,
            session_id=attempt_session_id,
            vocabulary_item_id=vocabulary_item_id,
            word=word,
            question_text=question_text,
            translations=tuple(translations or ()),
            updated_at=updated_at,
        )

    async def count_results(self, session_id: int) -> AttemptCounts:
        statement = (
            select(StudyAttempt.status, func.count())
            .where(
                StudyAttempt.session_id == session_id,
                StudyAttempt.status.in_(ANSWERED_STATUSES),
            )
            .group_by(StudyAttempt.status)
        )
        rows = (await self._get_session().execute(statement)).all()
        counts = {
            StudyAttemptStatus(status): count
            for status, count in rows
        }
        return AttemptCounts(
            correct=counts.get(StudyAttemptStatus.CORRECT, 0),
            incorrect=counts.get(StudyAttemptStatus.INCORRECT, 0),
            skipped=counts.get(StudyAttemptStatus.SKIPPED, 0)
        )

    async def delete_pending(self, session_id: int) -> None:
        await self._get_session().execute(
            delete(StudyAttempt).where(
                StudyAttempt.session_id == session_id,
                StudyAttempt.status == StudyAttemptStatus.PENDING,
            )
        )

    async def save_pending_answer(
        self,
        attempt_id: int,
        status: StudyAttemptStatus,
        answer_text: str,
        explanation_text: str | None,
    ) -> bool:
        result = await self._get_session().execute(
            update(StudyAttempt)
            .where(
                StudyAttempt.id == attempt_id,
                StudyAttempt.status == StudyAttemptStatus.PENDING,
            )
            .values(
                status=status,
                answer_text=answer_text,
                explanation_text=explanation_text,
            )
        )
        return result.rowcount > 0

    async def save(self, attempt: StudyAttempt) -> StudyAttempt:
        statement = (
            insert(StudyAttempt)
            .values(
                session_id=attempt.session_id,
                vocabulary_item_id=attempt.vocabulary_item_id,
                status=attempt.status,
                question_text=attempt.question_text,
                answer_text=attempt.answer_text,
                explanation_text=attempt.explanation_text,
            )
            .on_conflict_do_nothing()
            .returning(StudyAttempt)
        )
        saved_attempt = await self._get_session().scalar(statement)
        if saved_attempt is None:
            raise StudyAttemptAlreadyExistsError
        return saved_attempt
