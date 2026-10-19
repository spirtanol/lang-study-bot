from collections.abc import Awaitable, Callable

from taskiq import AsyncTaskiqDecoratedTask, Context, TaskiqDepends

from app.events.broker import get_brokers
from app.events.tasks.telegram import emit_telegram
from app.telegram import TelegramCommand


async def _handle(
    user_id: int,
    version: int,
    context: Context = TaskiqDepends(),
) -> None:
    container = context.state.container
    message = await container.user_reply_service.handle_command(
        user_id,
        TelegramCommand.STUDY,
        version,
    )
    if message is None:
        return
    await container.event_service.publish(
        emit_telegram(user_id, message),
    )


_task: AsyncTaskiqDecoratedTask = get_brokers().common_broker.register_task(
    _handle,
    task_name="study",
)


def emit_study(
    user_id: int,
    version: int,
) -> Callable[[], Awaitable[None]]:
    async def emit() -> None:
        await _task.kiq(user_id=user_id, version=version)

    return emit
