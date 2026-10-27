from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.defs import StartSessionResult, StudyAttemptStatus, StudySessionStatus
from app.graphs import AnswerCheckGraph
from app.llm import LLMError, LLMUnavailableError
from app.models import StudyAttempt, StudySession, User
from app.repositories import (
    ActiveStudySessionAlreadyExistsError,
    AttemptCounts,
    PendingQuestion,
    StudyAttemptAlreadyExistsError,
    StudyAttemptRepository,
    StudySessionRepository,
    VocabularyItemRepository,
)
from app.telegram.texts import (
    CHECK_FAILED_TEXT,
    CORRECT_COUNT_LABEL,
    CORRECT_TEXT,
    INCORRECT_COUNT_LABEL,
    INCORRECT_TEXT,
    MODEL_UNAVAILABLE_TEXT,
    NO_ACTIVE_SESSION_TEXT,
    POSSIBLE_TRANSLATIONS_TEXT,
    REVIEWED_COUNT_LABEL,
    RUSSIAN_REQUIRED_TEXT,
    SESSION_FINISHED_BY_TIME_TEXT,
    SESSION_FINISHED_TEXT,
    SESSION_INTERRUPTED_TEXT,
    SKIPPED_ANSWER,
    SKIPPED_COUNT_LABEL,
    START_PENDING_SESSION_TEXT,
    STUDY_LATER_TEXT,
)

from .exceptions import ActiveStudySessionNotFoundError, NoStudyWordsError
from .language_model import ASK_TRANSLATION_TEXT, LanguageModelService

QUESTION_PICK_ATTEMPTS = 3
PREVIOUS_QUESTIONS_LIMIT = 4


@dataclass(frozen=True, slots=True)
class StartSessionOutcome:
    result: StartSessionResult
    text: str


@dataclass(frozen=True, slots=True)
class AskTranslation:
    word: str
    text: str


@dataclass(frozen=True, slots=True)
class ReplyOutcome:
    text: str
    question: AskTranslation | None = None
    suggest_add_words: bool = False
    session_ended: bool = False


def _normalize_answer(text: str) -> str:
    return " ".join(text.strip().casefold().split())


def _matches_translation(answer: str, translations: tuple[str, ...]) -> bool:
    key = _normalize_answer(answer)
    if not key or not translations:
        return False
    return any(_normalize_answer(item) == key for item in translations)


def _correct_feedback(translations: tuple[str, ...]) -> str:
    items = [item.strip() for item in translations if item.strip()]
    if not items:
        return CORRECT_TEXT
    return f"{CORRECT_TEXT}. {POSSIBLE_TRANSLATIONS_TEXT} {', '.join(items)}."


def _skipped_feedback(translations: tuple[str, ...]) -> str:
    items = [item.strip() for item in translations if item.strip()]
    if not items:
        return SKIPPED_ANSWER
    return f"{SKIPPED_ANSWER}.\n\n{POSSIBLE_TRANSLATIONS_TEXT} {', '.join(items)}."


def _finish_text(
    feedback: str,
    counts: AttemptCounts,
    finished: str = SESSION_FINISHED_TEXT,
) -> str:
    reviewed = counts.correct + counts.incorrect
    return (
        f"{feedback}\n\n"
        f"{finished}\n"
        f"{REVIEWED_COUNT_LABEL} {reviewed}\n"
        f"{CORRECT_COUNT_LABEL} {counts.correct}\n"
        f"{INCORRECT_COUNT_LABEL} {counts.incorrect}\n"
        f"{SKIPPED_COUNT_LABEL} {counts.skipped}"
    )


def _interrupted_text(counts: AttemptCounts) -> str:
    reviewed = counts.correct + counts.incorrect
    return (
        f"{SESSION_INTERRUPTED_TEXT}\n"
        f"{REVIEWED_COUNT_LABEL} {reviewed}\n"
        f"{CORRECT_COUNT_LABEL} {counts.correct}\n"
        f"{INCORRECT_COUNT_LABEL} {counts.incorrect}\n"
        f"{SKIPPED_COUNT_LABEL} {counts.skipped}"
    )


class StudySessionService:
    def __init__(
        self,
        repository: StudySessionRepository,
        vocabulary_items: VocabularyItemRepository,
        study_attempts: StudyAttemptRepository,
        language_model: LanguageModelService,
        answer_check: AnswerCheckGraph,
        transaction: Callable[[], AbstractAsyncContextManager[None]],
        session_duration: timedelta,
    ):
        self._repository = repository
        self._vocabulary_items = vocabulary_items
        self._study_attempts = study_attempts
        self._language_model = language_model
        self._answer_check = answer_check
        self._transaction = transaction
        self._session_duration = session_duration

    async def start_session(self, user: User) -> StartSessionOutcome:
        async with self._transaction():
            active_session = await self._repository.get_latest_active(
                user.telegram_user_id,
            )
            if active_session is not None:
                if active_session.status == StudySessionStatus.PENDING:
                    active_session.status = StudySessionStatus.IN_PROGRESS
                    return StartSessionOutcome(
                        StartSessionResult.READY,
                        START_PENDING_SESSION_TEXT,
                    )
                return StartSessionOutcome(
                    StartSessionResult.ALREADY_READY,
                    "",
                )

            has_words = await self._vocabulary_items.exists_for_user(
                user.telegram_user_id,
            )
            if not has_words:
                raise NoStudyWordsError

            study_session = StudySession(
                user_id=user.telegram_user_id,
                status=StudySessionStatus.PENDING,
            )
            try:
                await self._repository.save(study_session)
            except ActiveStudySessionAlreadyExistsError:
                active_session = await self._repository.get_latest_active(
                    user.telegram_user_id,
                )
                if active_session is None:
                    raise
                if active_session.status == StudySessionStatus.PENDING:
                    active_session.status = StudySessionStatus.IN_PROGRESS
                    return StartSessionOutcome(
                        StartSessionResult.READY,
                        START_PENDING_SESSION_TEXT,
                    )
                return StartSessionOutcome(
                    StartSessionResult.ALREADY_READY,
                    "",
                )

            return StartSessionOutcome(
                StartSessionResult.READY,
                "",
            )

    async def get_next_question(self, user: User) -> AskTranslation | None:
        async with self._transaction():
            active_session = await self._repository.get_latest_active(
                user.telegram_user_id,
            )
            if active_session is None:
                raise ActiveStudySessionNotFoundError

            pending = await self._ask_pending(active_session.id)
            if pending is not None:
                return pending

            active_session.status = StudySessionStatus.IN_PROGRESS
            item = await self._vocabulary_items.pick_for_session(
                user.telegram_user_id,
                active_session.id,
            )
            if item is None:
                return None

            session_id = active_session.id

        attempt_number = 0
        while True:
            async with self._transaction():
                previous = await self._study_attempts.list_recent_question_texts(
                    item.vocabulary_item_id,
                    PREVIOUS_QUESTIONS_LIMIT,
                )
            question_text = await self._language_model.build_question_text(
                item.word,
                previous,
            )
            try:
                async with self._transaction():
                    await self._study_attempts.save(
                        StudyAttempt(
                            session_id=session_id,
                            vocabulary_item_id=item.vocabulary_item_id,
                            status=StudyAttemptStatus.PENDING,
                            question_text=question_text,
                        )
                    )
            except StudyAttemptAlreadyExistsError:
                async with self._transaction():
                    pending = await self._ask_pending(session_id)
                    if pending is not None:
                        return pending
                attempt_number += 1
                if attempt_number >= QUESTION_PICK_ATTEMPTS:
                    raise
                async with self._transaction():
                    item = await self._vocabulary_items.pick_for_session(
                        user.telegram_user_id,
                        session_id,
                    )
                    if item is None:
                        return None
                continue
            return AskTranslation(word=item.word, text=question_text)

    async def answer_pending(
        self,
        user: User,
        pending: PendingQuestion,
        text: str,
    ) -> ReplyOutcome:
        answer = text.strip()
        if not answer:
            return ReplyOutcome(ASK_TRANSLATION_TEXT)

        accepted = _matches_translation(answer, pending.translations)
        remarks = ""
        if not accepted:
            try:
                verdict = await self._answer_check.run(
                    pending.word,
                    answer,
                    pending.translations,
                )
            except LLMUnavailableError:
                return ReplyOutcome(MODEL_UNAVAILABLE_TEXT)
            except LLMError:
                return ReplyOutcome(CHECK_FAILED_TEXT)
            accepted = verdict.accepted
            remarks = verdict.remarks

        if accepted:
            feedback = _correct_feedback(pending.translations)
            explanation = None
            status = StudyAttemptStatus.CORRECT
            points_delta = 1
        else:
            feedback = (
                f"{INCORRECT_TEXT}\n{remarks.strip() or RUSSIAN_REQUIRED_TEXT}"
            )
            explanation = feedback
            status = StudyAttemptStatus.INCORRECT
            points_delta = -1

        async with self._transaction():
            saved = await self._study_attempts.save_pending_answer(
                pending.attempt_id,
                status,
                answer,
                explanation,
            )
            if saved:
                await self._vocabulary_items.add_points(
                    pending.vocabulary_item_id,
                    points_delta,
                )

        return await self._continue_after_answer(user, pending, feedback)

    async def skip_pending(
        self,
        user: User,
        pending: PendingQuestion,
    ) -> ReplyOutcome:
        async with self._transaction():
            saved = await self._study_attempts.save_pending_answer(
                pending.attempt_id,
                StudyAttemptStatus.SKIPPED,
                SKIPPED_ANSWER,
                None,
            )
            if saved:
                await self._vocabulary_items.add_points(
                    pending.vocabulary_item_id,
                    -1,
                )

        return await self._continue_after_answer(
            user,
            pending,
            _skipped_feedback(pending.translations),
        )

    async def interrupt(self, user: User) -> ReplyOutcome:
        async with self._transaction():
            active_session = await self._repository.get_latest_active(
                user.telegram_user_id,
            )
            if active_session is None:
                return ReplyOutcome(NO_ACTIVE_SESSION_TEXT)

            was_pending = active_session.status == StudySessionStatus.PENDING
            await self._study_attempts.delete_pending(active_session.id)
            if was_pending:
                reply = STUDY_LATER_TEXT
            else:
                counts = await self._study_attempts.count_results(active_session.id)
                reply = _interrupted_text(counts)
            await self._repository.interrupt(active_session.id)
        return ReplyOutcome(reply, session_ended=True)

    async def _continue_after_answer(
        self,
        user: User,
        pending: PendingQuestion,
        feedback: str,
    ) -> ReplyOutcome:
        expired = (
            pending.updated_at + self._session_duration
            <= datetime.now(timezone.utc)
        )
        if not expired:
            try:
                question = await self.get_next_question(user)
            except LLMUnavailableError:
                return ReplyOutcome(f"{feedback}\n\n{MODEL_UNAVAILABLE_TEXT}")
            if question is not None:
                return ReplyOutcome(feedback, question)

        finished = (
            SESSION_FINISHED_BY_TIME_TEXT if expired else SESSION_FINISHED_TEXT
        )
        async with self._transaction():
            counts = await self._study_attempts.count_results(pending.session_id)
            await self._repository.complete(pending.session_id)
        return ReplyOutcome(
            _finish_text(feedback, counts, finished),
            session_ended=True,
        )

    async def _ask_pending(self, session_id: int) -> AskTranslation | None:
        pending = await self._study_attempts.get_pending(session_id)
        if pending is None:
            return None
        return AskTranslation(word=pending.word, text=pending.question_text)
