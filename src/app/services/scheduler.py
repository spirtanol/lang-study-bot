import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from datetime import datetime, timedelta, timezone

from app.repositories import UserRepository

from .events import EventService

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(
        self,
        users: UserRepository,
        events: EventService,
        transaction: Callable[[], AbstractAsyncContextManager[None]],
        lease: timedelta,
    ):
        self._users = users
        self._events = events
        self._transaction = transaction
        self._lease = lease

    async def dispatch_due(self) -> None:
        from app.events.tasks import emit_schedule

        try:
            due = await self._claim_due()
        except Exception:
            logger.exception("Не удалось захватить просроченные запуски")
            return

        for user_telegram_id, version in due:
            try:
                await self._events.publish(emit_schedule(user_telegram_id, version))
            except Exception:
                logger.exception(
                    "Не удалось опубликовать событие расписания для пользователя %s",
                    user_telegram_id,
                )

    async def _claim_due(self) -> list[tuple[int, int]]:
        now = datetime.now(timezone.utc)
        async with self._transaction():
            users = await self._users.lock_due(now)
            due = [(user.telegram_user_id, user.version) for user in users]
            for user in users:
                user.next_run_at = now + self._lease
            return due
