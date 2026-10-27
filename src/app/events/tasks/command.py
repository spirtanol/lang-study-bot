from collections.abc import Awaitable, Callable

from taskiq import AsyncTaskiqDecoratedTask, Context, TaskiqDepends

from app.events.broker import get_brokers
from app.events.tasks.telegram import emit_telegram
from app.services.exceptions import UserBusyError, UserVersionError


async def _handle(
    user_id: int,
    command: str,
    context: Context = TaskiqDepends(),
) -> None:
    container = context.state.container
    async with container.transaction():
        user = await container.user_repository.get_by_id(user_id)
        if user is None:
            return
        version = user.version
    try:
        message = await container.user_reply_service.handle_command(
            user_id,
            command,
            version,
        )
    except UserVersionError:
        return
    if message is None:
        return
    await container.event_service.publish(
        emit_telegram(user_id, message),
    )


_task: AsyncTaskiqDecoratedTask = get_brokers().common_broker.register_task(
    _handle,
    task_name="command",
    retry_on_error=True,
    max_retries=8,
    types_of_exceptions=(UserBusyError,),
)


def emit_command(
    user_id: int,
    command: str,
) -> Callable[[], Awaitable[None]]:
    async def emit() -> None:
        await _task.kiq(user_id=user_id, command=command)

    return emit
