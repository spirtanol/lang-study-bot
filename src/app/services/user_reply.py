import re
from collections.abc import Callable, Sequence
from contextlib import AbstractAsyncContextManager
from typing import assert_never
from uuid import UUID

from app.defs import StartSessionResult, StudySessionStatus, UserIntent
from app.llm import LLMError, LLMUnavailableError
from app.models import StudyScheduleSlot, User, Word
from app.repositories import (
    PendingQuestion,
    StudyAttemptRepository,
    StudySessionRepository,
    UserRepository,
)
from app.telegram import TelegramCommand, TelegramMessage
from app.telegram.reply import (
    ADD_WORDS_MARKUP,
    CANCEL_MARKUP,
    QUESTION_REPLY_MARKUP,
    WELCOME,
    add_batch_markup,
)
from app.telegram.texts import (
    ADD_WORDS_PARSE_FAILED_TEXT,
    ADD_WORDS_PROMPT,
    ADDED_WORDS_LABEL,
    ALREADY_IN_PROGRESS_TEXT,
    CANCELLED_TEXT,
    CHECK_FAILED_TEXT,
    CONTACTS_TEXT,
    MODEL_UNAVAILABLE_TEXT,
    NO_SCHEDULE_TEXT,
    NO_STUDY_WORDS_TEXT,
    NO_WORDS_TEXT,
    QUESTION_TEXT,
    REJECTED_WORDS_LABEL,
    SCHEDULE_CHANGED_TEXT,
    SCHEDULE_CLEARED_TEXT,
    SCHEDULE_DAILY,
    SCHEDULE_DAILY_TITLE,
    SCHEDULE_PARSE_FAILED_TEXT,
    SCHEDULE_TIME_PROMPT,
    START_STUDY_TEXT,
    TIMEZONE_LABEL,
    TIMEZONE_PARSE_FAILED_TEXT,
    TIMEZONE_PROMPT,
    TIMEZONE_SET_TEXT,
    WORD_BATCH_EXPIRED_TEXT,
    WORDS_ADDED_TEXT,
)

from .exceptions import (
    NoStudyWordsError,
    PendingQuestionNotFoundError,
    UserVersionError,
    WordNotAdded,
)
from .language_model import LanguageModelService
from .study_schedule import StudyScheduleService
from .user import UserService
from .study_session import (
    AskTranslation,
    ReplyOutcome,
    StudySessionService,
)
from .vocabulary import VocabularyService
from .word import WordService
from .word_add_batch import WordAddBatchService

_LOCKED_COMMANDS = {
    TelegramCommand.SCHEDULE,
    TelegramCommand.SETUP_SCHEDULE,
    TelegramCommand.CLEAR_SCHEDULE,
    TelegramCommand.TIMEZONE,
    TelegramCommand.CANCEL,
    TelegramCommand.ADD_WORDS,
    TelegramCommand.STUDY,
    TelegramCommand.DONT_KNOW,
    TelegramCommand.FINISH,
}
_WORD_SPLIT = re.compile(r"[,;\r\n]+")


class UserReplyService:
    def __init__(
        self,
        sessions: StudySessionRepository,
        attempts: StudyAttemptRepository,
        study_sessions: StudySessionService,
        language_model: LanguageModelService,
        users: UserRepository,
        user_service: UserService,
        schedule: StudyScheduleService,
        vocabulary: VocabularyService,
        words: WordService,
        batches: WordAddBatchService,
        transaction: Callable[[], AbstractAsyncContextManager[None]],
        contact_telegram_username: str,
        contact_email: str,
    ):
        self._sessions = sessions
        self._attempts = attempts
        self._study_sessions = study_sessions
        self._language_model = language_model
        self._users = users
        self._user_service = user_service
        self._schedule = schedule
        self._vocabulary = vocabulary
        self._words = words
        self._batches = batches
        self._transaction = transaction
        self._contact_telegram_username = contact_telegram_username
        self._contact_email = contact_email

    async def handle_command(
        self,
        user_id: int,
        command: str,
        version: int | None = None,
    ) -> TelegramMessage | None:
        name, _, params = command.partition(":")
        if name == TelegramCommand.ADD_BATCH:
            return await self._add_batch(user_id, params)
        if name == TelegramCommand.START:
            return WELCOME
        if name == TelegramCommand.CONTACTS:
            return TelegramMessage(
                text=CONTACTS_TEXT.format(
                    telegram=self._contact_telegram_username,
                    email=self._contact_email,
                ),
            )
        if name not in _LOCKED_COMMANDS:
            return None

        async with self._transaction():
            user = await self._users.lock_user(user_id)
            if user is None:
                return None
            match name:
                case TelegramCommand.SCHEDULE:
                    slots = await self._schedule.get_schedule(user_id)
                    return TelegramMessage(
                        text=_schedule_text(user.timezone, slots, SCHEDULE_DAILY),
                    )
                case TelegramCommand.SETUP_SCHEDULE:
                    user.intent = UserIntent.SCHEDULE
                    await self._users.save(user)
                    return TelegramMessage(
                        text=SCHEDULE_TIME_PROMPT,
                        reply_markup=CANCEL_MARKUP,
                    )
                case TelegramCommand.CLEAR_SCHEDULE:
                    await self._schedule.clear(user_id)
                    return TelegramMessage(text=SCHEDULE_CLEARED_TEXT)
                case TelegramCommand.TIMEZONE:
                    user.intent = UserIntent.TIMEZONE
                    await self._users.save(user)
                    return TelegramMessage(
                        text=TIMEZONE_PROMPT,
                        reply_markup=CANCEL_MARKUP,
                    )
                case TelegramCommand.CANCEL:
                    active_session = await self._sessions.get_latest_active(user_id)
                    pending = None
                    if active_session is not None:
                        pending = await self._attempts.get_pending(active_session.id)
                    if pending is None:
                        user.intent = UserIntent.UNKNOWN
                    else:
                        user.intent = UserIntent.ANSWER
                    await self._users.save(user)
                    return TelegramMessage(text=CANCELLED_TEXT)
                case TelegramCommand.ADD_WORDS:
                    user.intent = UserIntent.ADD_WORDS
                    await self._users.save(user)
                    return TelegramMessage(
                        text=ADD_WORDS_PROMPT,
                        reply_markup=CANCEL_MARKUP,
                    )
                case TelegramCommand.FINISH:
                    outcome = await self._study_sessions.interrupt(user)
                    return TelegramMessage(text=outcome.text)
                case TelegramCommand.STUDY:
                    user.intent = UserIntent.STUDY
                    await self._users.save(user)
                case TelegramCommand.DONT_KNOW:
                    pass
                case _:
                    return None
        match name:
            case TelegramCommand.STUDY:
                reply = await self._start_study(user)
            case TelegramCommand.DONT_KNOW:
                reply = await self.handle_skip(user_id, version)
            case _:
                return None
        parts: list[str] = []
        reply_markup = None
        if reply.text:
            parts.append(reply.text)
        if reply.question is not None:
            parts.append(
                QUESTION_TEXT.format(
                    word=reply.question.word,
                    text=reply.question.text,
                ),
            )
            reply_markup = QUESTION_REPLY_MARKUP
        elif reply.suggest_add_words:
            reply_markup = ADD_WORDS_MARKUP
        return TelegramMessage(
            text="\n\n".join(parts),
            reply_markup=reply_markup,
        )

    async def show_schedule(self, user: User) -> ReplyOutcome:
        slots = await self._schedule.get_schedule(user.telegram_user_id)
        return ReplyOutcome(
            _schedule_text(user.timezone, slots, SCHEDULE_DAILY_TITLE),
        )

    async def handle_translate(
        self,
        user_id: int,
        version: int,
        text: str,
    ) -> TelegramMessage | None:
        if not await self._has_version(user_id, version):
            raise UserVersionError

        try:
            is_list = await self._language_model.is_word_list(text)
        except LLMUnavailableError:
            return await self._unavailable_reply(user_id, version)
        except LLMError:
            return None
        if not is_list:
            return None

        accepted: list[Word] = []
        seen: set[int] = set()
        for word_text in _split_words(text):
            try:
                word = await self._words.get_or_create(word_text)
            except WordNotAdded:
                continue
            except LLMUnavailableError:
                return await self._unavailable_reply(user_id, version)
            except LLMError:
                continue
            if word.id in seen:
                continue
            seen.add(word.id)
            accepted.append(word)
        if not accepted:
            return None

        batch_id = await self._batches.add([word.id for word in accepted])
        if not await self._has_version(user_id, version):
            await self._batches.remove_batch(batch_id)
            raise UserVersionError
        return TelegramMessage(
            text=_word_translation_lines(accepted),
            reply_markup=add_batch_markup(batch_id),
        )

    async def _add_batch(self, user_id: int, batch: str) -> TelegramMessage:
        try:
            batch_id = UUID(batch)
        except ValueError:
            return TelegramMessage(text=WORD_BATCH_EXPIRED_TEXT)
        word_ids = await self._batches.word_ids(batch_id)
        if not word_ids:
            return TelegramMessage(text=WORD_BATCH_EXPIRED_TEXT)
        await self._vocabulary.add_by_ids(user_id, word_ids)
        await self._batches.remove_batch(batch_id)
        return TelegramMessage(text=WORDS_ADDED_TEXT)

    async def _has_version(self, user_id: int, version: int) -> bool:
        async with self._transaction():
            user = await self._users.lock_for_version(user_id, version)
            return user is not None

    async def _unavailable_reply(
        self,
        user_id: int,
        version: int,
    ) -> TelegramMessage:
        if not await self._has_version(user_id, version):
            raise UserVersionError
        return TelegramMessage(text=MODEL_UNAVAILABLE_TEXT)

    async def handle_add_words(
        self,
        user_id: int,
        version: int | None,
        text: str,
    ) -> ReplyOutcome:
        words = _split_words(text)
        if not words:
            return ReplyOutcome(ADD_WORDS_PROMPT)

        added: list[Word] = []
        rejected: list[tuple[str, str]] = []
        pending: PendingQuestion | None = None
        try:
            for word in words:
                try:
                    added.append(await self._vocabulary.add_item(user_id, word))
                except WordNotAdded as error:
                    rejected.append((word, error.reason))

            async with self._transaction():
                user = await self._users.lock_for_version(user_id, version) if version is not None else await self._users.lock_user(user_id)
                if user is None:
                    raise UserVersionError

                active_session = await self._sessions.get_latest_active(
                    user.telegram_user_id,
                )
                if active_session is not None:
                    pending = await self._attempts.get_pending(active_session.id)
                if pending is None:
                    user.intent = UserIntent.UNKNOWN
                else:
                    user.intent = UserIntent.ANSWER
                if version is not None:
                    user.version += 1
                await self._users.save(user)
        except LLMUnavailableError:
            return ReplyOutcome(MODEL_UNAVAILABLE_TEXT)
        except LLMError:
            return ReplyOutcome(ADD_WORDS_PARSE_FAILED_TEXT)
        return ReplyOutcome(_add_words_reply(added, rejected), _pending_ask(pending))

    async def handle_answer(
        self,
        user_id: int,
        version: int | None,
        text: str,
    ) -> ReplyOutcome:
        async with self._transaction():
            user = (
                await self._users.lock_for_version(user_id, version)
                if version is not None
                else await self._users.lock_user(user_id)
            )
            if user is None:
                raise UserVersionError

            pending = await self._pending_question(user)
            if pending is None:
                raise PendingQuestionNotFoundError

        outcome = await self._study_sessions.answer_pending(user, pending, text)
        if outcome.text in {CHECK_FAILED_TEXT, MODEL_UNAVAILABLE_TEXT}:
            return outcome
        if version is not None:
            async with self._transaction():
                if not await self._users.bump_version(user_id, version):
                    raise UserVersionError
        return outcome

    async def handle_schedule(
        self,
        user_id: int,
        version: int | None,
        text: str,
    ) -> ReplyOutcome:
        answer = text.strip()
        if not answer:
            return ReplyOutcome(SCHEDULE_TIME_PROMPT)
        try:
            local_time = await self._language_model.parse_clock_time(answer)
        except LLMUnavailableError:
            return ReplyOutcome(MODEL_UNAVAILABLE_TEXT)
        except LLMError:
            return ReplyOutcome(SCHEDULE_PARSE_FAILED_TEXT)
        if local_time is None:
            return ReplyOutcome(SCHEDULE_TIME_PROMPT)

        async with self._transaction():
            user = await self._users.lock_for_version(user_id, version) if version is not None else await self._users.lock_user(user_id)
            if user is None:
                raise UserVersionError
            await self._schedule.set_daily(user_id, local_time)
            active_session = await self._sessions.get_latest_active(
                user.telegram_user_id,
            )
            pending = None
            if active_session is None:
                user.intent = UserIntent.UNKNOWN
            else:
                user.intent = UserIntent.ANSWER
                pending = await self._attempts.get_pending(active_session.id)
            if version is not None:
                user.version += 1
            await self._users.save(user)
        shown = await self.show_schedule(user)
        return ReplyOutcome(
            f"{SCHEDULE_CHANGED_TEXT}\n{shown.text}",
            _pending_ask(pending),
        )

    async def handle_timezone(
        self,
        user_id: int,
        version: int | None,
        text: str,
    ) -> ReplyOutcome:
        answer = text.strip()
        if not answer:
            return ReplyOutcome(TIMEZONE_PROMPT)
        try:
            zone = await self._language_model.resolve_timezone(answer)
        except LLMUnavailableError:
            return ReplyOutcome(MODEL_UNAVAILABLE_TEXT)
        except LLMError:
            return ReplyOutcome(TIMEZONE_PARSE_FAILED_TEXT)
        if zone is None:
            return ReplyOutcome(TIMEZONE_PARSE_FAILED_TEXT)

        async with self._transaction():
            user = (
                await self._users.lock_for_version(user_id, version)
                if version is not None
                else await self._users.lock_user(user_id)
            )
            if user is None:
                raise UserVersionError
            user.timezone = zone
            active_session = await self._sessions.get_latest_active(
                user.telegram_user_id,
            )
            pending = None
            if active_session is not None:
                pending = await self._attempts.get_pending(active_session.id)
            if pending is None:
                user.intent = UserIntent.UNKNOWN
            else:
                user.intent = UserIntent.ANSWER
            if version is not None:
                user.version += 1
            await self._users.save(user)
            await self._user_service.refresh_next_run(user_id)
        return ReplyOutcome(
            f"{TIMEZONE_SET_TEXT} {zone}.",
            _pending_ask(pending),
        )

    async def _start_study(self, user: User) -> ReplyOutcome:
        try:
            outcome = await self._study_sessions.start_session(user)
        except NoStudyWordsError:
            return ReplyOutcome(NO_STUDY_WORDS_TEXT, suggest_add_words=True)
        match outcome.result:
            case StartSessionResult.NOT_NOW:
                return ReplyOutcome(outcome.text)
            case StartSessionResult.READY:
                already_ready = False
            case StartSessionResult.ALREADY_READY:
                already_ready = True
            case _ as unexpected:
                assert_never(unexpected)

        try:
            question = await self._study_sessions.get_next_question(user)
        except LLMUnavailableError:
            return ReplyOutcome(MODEL_UNAVAILABLE_TEXT)
        await self._user_service.refresh_next_run(user.telegram_user_id)
        if question is None:
            return ReplyOutcome(NO_WORDS_TEXT)
        if already_ready:
            question = AskTranslation(
                word=question.word,
                text=f"{ALREADY_IN_PROGRESS_TEXT}\n{question.text}",
            )
            return ReplyOutcome("", question)
        return ReplyOutcome(outcome.text or START_STUDY_TEXT, question)

    async def handle_skip(
        self,
        user_id: int,
        version: int | None,
    ) -> ReplyOutcome:
        async with self._transaction():
            user = (
                await self._users.lock_for_version(user_id, version)
                if version is not None
                else await self._users.lock_user(user_id)
            )
            if user is None:
                raise UserVersionError

            pending = await self._pending_question(user)
            if pending is None:
                raise PendingQuestionNotFoundError

        outcome = await self._study_sessions.skip_pending(user, pending)
        if version is not None:
            async with self._transaction():
                if not await self._users.bump_version(user_id, version):
                    raise UserVersionError
        return outcome

    async def _pending_question(self, user: User) -> PendingQuestion | None:
        async with self._transaction():
            active_session = await self._sessions.get_latest_active(
                user.telegram_user_id,
            )
            if (
                active_session is None
                or active_session.status != StudySessionStatus.IN_PROGRESS
            ):
                return None
            return await self._attempts.get_pending(active_session.id)


def _schedule_text(
    timezone_name: str | None,
    slots: Sequence[StudyScheduleSlot],
    daily: str,
) -> str:
    lines = [f"{TIMEZONE_LABEL} {timezone_name or UserService.DEFAULT_TIMEZONE}"]
    if slots:
        lines.extend(
            f"{daily} {slot.local_time.strftime('%H:%M')}" for slot in slots
        )
    else:
        lines.append(NO_SCHEDULE_TEXT)
    return "\n".join(lines)


def _split_words(text: str) -> list[str]:
    seen: set[str] = set()
    words: list[str] = []
    for part in _WORD_SPLIT.split(text):
        word = " ".join(part.split())
        key = word.lower()
        if not word or key in seen:
            continue
        seen.add(key)
        words.append(word)
    return words


def _word_translation_lines(words: Sequence[Word]) -> str:
    lines: list[str] = []
    for word in words:
        translations = ", ".join(word.translations)
        if translations:
            lines.append(f"{word.text} — {translations}.")
        else:
            lines.append(f"{word.text}.")
    return "\n".join(lines)


def _add_words_reply(added: list[Word], rejected: list[tuple[str, str]]) -> str:
    parts: list[str] = []
    if added:
        lines = [ADDED_WORDS_LABEL]
        for word in added:
            translations = ", ".join(word.translations)
            if translations:
                lines.append(f"{word.text} — {translations}.")
            else:
                lines.append(f"{word.text}.")
        parts.append("\n".join(lines))
    if rejected:
        lines = [REJECTED_WORDS_LABEL]
        lines.extend(f"{word} — {reason}." for word, reason in rejected)
        parts.append("\n".join(lines))
    return "\n".join(parts)


def _pending_ask(pending: PendingQuestion | None) -> AskTranslation | None:
    if pending is None:
        return None
    return AskTranslation(word=pending.word, text=pending.question_text)
