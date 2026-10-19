from collections.abc import Awaitable, Callable

from taskiq import AsyncTaskiqDecoratedTask, Context, TaskiqDepends

from app.events.broker import get_brokers
from app.events.tasks.telegram import emit_telegram
from app.services.exceptions import UserVersionError
from app.telegram import TelegramMessage


async def _handle(
    user_id: int,
    version: int,
    text: str,
    context: Context = TaskiqDepends(),
) -> None:
    container = context.state.container
    try:
        reply = await container.user_reply_service.handle_add_words(
            user_id,
            version,
            text,
        )
    except UserVersionError:
        return
    await container.event_service.publish(
        emit_telegram(user_id, TelegramMessage(text=reply.text)),
    )


_task: AsyncTaskiqDecoratedTask = get_brokers().common_broker.register_task(
    _handle,
    task_name="add_words",
)


def emit_add_words(
    user_id: int,
    version: int,
    text: str,
) -> Callable[[], Awaitable[None]]:
    async def emit() -> None:
        await _task.kiq(user_id=user_id, version=version, text=text)

    return emit
