from collections.abc import Awaitable, Callable

from taskiq import AsyncTaskiqDecoratedTask, Context, TaskiqDepends

from app.events.broker import get_brokers
from app.events.tasks.telegram import emit_telegram
from app.services.exceptions import (
    PendingQuestionNotFoundError,
    UserBusyError,
    UserVersionError,
)
from app.telegram import TelegramCommand


async def _handle(
    user_id: int,
    version: int,
    context: Context = TaskiqDepends(),
) -> None:
    container = context.state.container
    try:
        message = await container.user_reply_service.handle_command(
            user_id,
            TelegramCommand.DONT_KNOW,
            version,
        )
    except (PendingQuestionNotFoundError, UserVersionError):
        return
    if message is None:
        return
    await container.event_service.publish(
        emit_telegram(user_id, message),
    )


_task: AsyncTaskiqDecoratedTask = get_brokers().common_broker.register_task(
    _handle,
    task_name="dont_know",
    retry_on_error=True,
    max_retries=8,
    types_of_exceptions=(UserBusyError,),
)


def emit_dont_know(
    user_id: int,
    version: int,
) -> Callable[[], Awaitable[None]]:
    async def emit() -> None:
        await _task.kiq(user_id=user_id, version=version)

    return emit
