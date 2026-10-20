from collections.abc import Awaitable, Callable

from taskiq import AsyncTaskiqDecoratedTask, Context, TaskiqDepends

from app.events.broker import get_brokers


async def _handle(context: Context = TaskiqDepends()) -> None:
    await context.state.container.chat_message_service.delete_old()


_task: AsyncTaskiqDecoratedTask = get_brokers().common_broker.register_task(
    _handle,
    task_name="delete_old_chat_messages",
)


def emit_delete_old_chat_messages() -> Callable[[], Awaitable[None]]:
    async def emit() -> None:
        await _task.kiq()

    return emit
