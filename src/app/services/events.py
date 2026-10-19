from collections.abc import Awaitable, Callable

from app.events.broker import get_brokers


class EventService:
    def __init__(self) -> None:
        self._ensured = False

    async def publish(self, emit: Callable[[], Awaitable[None]]) -> None:
        await self._ensure_started()
        await emit()

    async def _ensure_started(self) -> None:
        if self._ensured:
            return
        brokers = get_brokers()
        for broker in (brokers.common_broker, brokers.telegram_broker):
            if broker.write_conn is not None:
                continue
            await broker.startup()
        self._ensured = True
