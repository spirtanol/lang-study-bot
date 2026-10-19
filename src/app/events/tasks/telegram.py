from collections.abc import Awaitable, Callable

from taskiq import AsyncTaskiqDecoratedTask, Context, TaskiqDepends

from app.events.broker import get_brokers
from app.services.exceptions import TelegramSendError
from app.telegram import TelegramMessage


async def _send(
    chat_id: int,
    message: TelegramMessage,
    context: Context = TaskiqDepends(),
) -> None:
    try:
        await context.state.container.telegram_message_service.send(chat_id, message)
    except Exception as exc:
        raise TelegramSendError from exc


_task: AsyncTaskiqDecoratedTask = get_brokers().telegram_broker.register_task(
    _send,
    task_name="telegram",
    retry_on_error=True,
    max_retries=3,
    types_of_exceptions=(TelegramSendError,),
)


def emit_telegram(
    chat_id: int,
    message: TelegramMessage,
) -> Callable[[], Awaitable[None]]:
    async def emit() -> None:
        await _task.kiq(chat_id=chat_id, message=message)

    return emit
