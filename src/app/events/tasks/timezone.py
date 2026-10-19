from collections.abc import Awaitable, Callable

from taskiq import AsyncTaskiqDecoratedTask, Context, TaskiqDepends

from app.events.broker import get_brokers
from app.events.tasks.telegram import emit_telegram
from app.services.exceptions import UserVersionError
from app.telegram import TelegramMessage
from app.telegram.reply import CANCEL_MARKUP
from app.telegram.texts import TIMEZONE_PARSE_FAILED_TEXT, TIMEZONE_PROMPT


async def _handle(
    user_id: int,
    version: int,
    text: str,
    context: Context = TaskiqDepends(),
) -> None:
    container = context.state.container
    try:
        reply = await container.user_reply_service.handle_timezone(
            user_id,
            version,
            text,
        )
    except UserVersionError:
        return
    reply_markup = None
    if reply.text in {TIMEZONE_PROMPT, TIMEZONE_PARSE_FAILED_TEXT}:
        reply_markup = CANCEL_MARKUP
    await container.event_service.publish(
        emit_telegram(
            user_id,
            TelegramMessage(text=reply.text, reply_markup=reply_markup),
        ),
    )


_task: AsyncTaskiqDecoratedTask = get_brokers().common_broker.register_task(
    _handle,
    task_name="timezone",
)


def emit_timezone(
    user_id: int,
    version: int,
    text: str,
) -> Callable[[], Awaitable[None]]:
    async def emit() -> None:
        await _task.kiq(user_id=user_id, version=version, text=text)

    return emit
