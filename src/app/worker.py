from taskiq import SmartRetryMiddleware, TaskiqEvents, TaskiqState
from taskiq_aio_pika import AioPikaBroker

from app.core.config import get_config
from app.core.container import Container
from app.core.disposer import dispose
from app.core.logging import init_logging
from app.events.broker import get_brokers
from app.events.user_context import UserContextMiddleware

init_logging()


async def _startup(state: TaskiqState) -> None:
    state.container = Container(config=get_config())


async def _shutdown(_state: TaskiqState) -> None:
    await dispose()


def worker_common_broker() -> AioPikaBroker:
    return (
        get_brokers().common_broker
        .with_middlewares(
            SmartRetryMiddleware(
                default_retry_count=3,
                use_delay_exponent=True,
                max_delay_exponent=60,
            ),
            UserContextMiddleware(),
        )
        .with_event_handlers(TaskiqEvents.WORKER_STARTUP, _startup)
        .with_event_handlers(TaskiqEvents.WORKER_SHUTDOWN, _shutdown)
    )


def worker_telegram_broker() -> AioPikaBroker:
    return (
        get_brokers().telegram_broker
        .with_middlewares(
            SmartRetryMiddleware(
                default_retry_count=3,
                use_delay_exponent=True,
                max_delay_exponent=60,
            ),
            UserContextMiddleware(),
        )
        .with_event_handlers(TaskiqEvents.WORKER_STARTUP, _startup)
        .with_event_handlers(TaskiqEvents.WORKER_SHUTDOWN, _shutdown)
    )
