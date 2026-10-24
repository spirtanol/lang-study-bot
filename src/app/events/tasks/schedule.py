from collections.abc import Awaitable, Callable, Sequence
from datetime import datetime, time, timedelta, timezone

from taskiq import AsyncTaskiqDecoratedTask, Context, TaskiqDepends

from app.defs import SCHEDULE_START_WINDOW, StudyAttemptStatus, StudySessionStatus
from app.events.broker import get_brokers
from app.events.tasks.telegram import emit_telegram
from app.models import StudyScheduleSlot
from app.services.exceptions import NoStudyWordsError
from app.telegram import TelegramMessage
from app.telegram.reply import ADD_WORDS_MARKUP, STUDY_TIME_MARKUP
from app.telegram.texts import (
    CORRECT_COUNT_LABEL,
    INCORRECT_COUNT_LABEL,
    REVIEWED_COUNT_LABEL,
    SESSION_FINISHED_TIMEOUT_TEXT,
    SESSION_MISSED_DUE_TIMEOUT_TEXT,
    SESSION_MISSED_TIMEOUT_TEXT,
    STUDY_TIME_NO_WORDS_TEXT,
    STUDY_TIME_TEXT,
)


async def _handle(
    user_telegram_id: int,
    version: int,
    context: Context = TaskiqDepends(),
) -> None:
    container = context.state.container
    timeout = timedelta(minutes=container.config.session_timeout_minutes)
    now = datetime.now(timezone.utc)
    message: str | None = None
    with_study_buttons = False
    with_add_words_button = False

    async with container.transaction():
        user = await container.user_repository.lock_for_version(
            user_telegram_id,
            version,
        )
        if user is None:
            return

        session = await container.study_session_repository.get_latest_active(
            user.telegram_user_id,
        )
        if session is None:
            slots = await container.study_schedule_slot_repository.list_for_user(
                user.telegram_user_id,
            )
            if slots:
                local_now = user.local_now()
                previous = _previous_run_at(slots, local_now)
                if local_now - previous <= SCHEDULE_START_WINDOW:
                    try:
                        await container.study_session_service.start_session(user)
                    except NoStudyWordsError:
                        message = STUDY_TIME_NO_WORDS_TEXT
                        with_add_words_button = True
                    else:
                        message = STUDY_TIME_TEXT
                        with_study_buttons = True
        elif session.status == StudySessionStatus.PENDING:
            if session.created_at + timeout <= now:
                session.status = StudySessionStatus.TIMED_OUT
                message = SESSION_MISSED_TIMEOUT_TEXT
        elif session.status == StudySessionStatus.IN_PROGRESS:
            attempt = await container.study_attempt_repository.get_latest(
                session.id,
            )
            if attempt is not None:
                if attempt.updated_at + timeout <= now:
                    attempt.status = StudyAttemptStatus.TIMED_OUT
                    session.status = StudySessionStatus.TIMED_OUT
                    counts = await container.study_attempt_repository.count_results(
                        session.id,
                    )
                    reviewed = counts.correct + counts.incorrect
                    message = (
                        f"{SESSION_FINISHED_TIMEOUT_TEXT}\n"
                        f"{REVIEWED_COUNT_LABEL} {reviewed}\n"
                        f"{CORRECT_COUNT_LABEL} {counts.correct}\n"
                        f"{INCORRECT_COUNT_LABEL} {counts.incorrect}"
                    )
            elif session.updated_at + timeout <= now:
                session.status = StudySessionStatus.TIMED_OUT
                message = SESSION_FINISHED_TIMEOUT_TEXT
        elif session.status == StudySessionStatus.DEFERRED:
            if session.updated_at + timeout <= now:
                session.status = StudySessionStatus.DEFERRED_2
                message = STUDY_TIME_TEXT
                with_study_buttons = True
        elif session.status == StudySessionStatus.DEFERRED_2:
            if session.updated_at + timeout <= now:
                session.status = StudySessionStatus.TIMED_OUT
                message = SESSION_MISSED_DUE_TIMEOUT_TEXT

        await container.user_service.refresh_next_run(user_telegram_id)
        await container.user_repository.bump_version(
            user_telegram_id,
            version,
        )

    if message is not None:
        if with_add_words_button:
            reply_markup = ADD_WORDS_MARKUP
        elif with_study_buttons:
            reply_markup = STUDY_TIME_MARKUP
        else:
            reply_markup = None
        await container.event_service.publish(
            emit_telegram(
                user_telegram_id,
                TelegramMessage(text=message, reply_markup=reply_markup),
            ),
        )


_task: AsyncTaskiqDecoratedTask = get_brokers().common_broker.register_task(
    _handle,
    task_name="schedule",
)


def emit_schedule(
    user_telegram_id: int,
    version: int,
) -> Callable[[], Awaitable[None]]:
    async def emit() -> None:
        await _task.kiq(user_telegram_id=user_telegram_id, version=version)

    return emit


def _previous_run_at(
    slots: Sequence[StudyScheduleSlot],
    local_now: datetime,
) -> datetime:
    return max(
        _previous_occurrence(local_now, slot.local_time) for slot in slots
    )


def _previous_occurrence(local_now: datetime, local_time: time) -> datetime:
    candidate = datetime.combine(
        local_now.date(),
        local_time.replace(tzinfo=None),
        tzinfo=local_now.tzinfo,
    )
    if candidate > local_now:
        candidate -= timedelta(days=1)
    return candidate
