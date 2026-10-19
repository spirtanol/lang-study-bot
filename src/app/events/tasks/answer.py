from collections.abc import Awaitable, Callable

from taskiq import AsyncTaskiqDecoratedTask, Context, TaskiqDepends

from app.events.broker import get_brokers
from app.events.tasks.telegram import emit_telegram
from app.services.exceptions import PendingQuestionNotFoundError, UserVersionError
from app.telegram import TelegramMessage
from app.telegram.reply import QUESTION_REPLY_MARKUP
from app.telegram.texts import QUESTION_TEXT


async def _handle(
    user_id: int,
    version: int,
    text: str,
    context: Context = TaskiqDepends(),
) -> None:
    container = context.state.container
    try:
        reply = await container.user_reply_service.handle_answer(
            user_id,
            version,
            text,
        )
    except (PendingQuestionNotFoundError, UserVersionError):
        return
    parts: list[str] = []
    reply_markup = None
    if reply.text:
        parts.append(reply.text)
    if reply.question is not None:
        parts.append(
            QUESTION_TEXT.format(word=reply.question.word, text=reply.question.text),
        )
        reply_markup = QUESTION_REPLY_MARKUP
    if not parts:
        return
    await container.event_service.publish(
        emit_telegram(
            user_id,
            TelegramMessage(text="\n\n".join(parts), reply_markup=reply_markup),
        ),
    )


_task: AsyncTaskiqDecoratedTask = get_brokers().common_broker.register_task(
    _handle,
    task_name="answer",
)


def emit_answer(
    user_id: int,
    version: int,
    text: str,
) -> Callable[[], Awaitable[None]]:
    async def emit() -> None:
        await _task.kiq(user_id=user_id, version=version, text=text)

    return emit
