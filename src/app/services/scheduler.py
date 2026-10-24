import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from datetime import datetime, timedelta, timezone

from app.core.logging import user_telegram_id as log_user_id
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
        self._next_chat_cleanup: datetime | None = None
        self._next_batch_cleanup: datetime | None = None

    async def run(self) -> None:
        await self.dispatch_due()
        await self._publish_chat_cleanup()
        await self._publish_batch_cleanup()

    async def _publish_chat_cleanup(self) -> None:
        from app.events.tasks import emit_delete_old_chat_messages

        now = datetime.now(timezone.utc)
        if self._next_chat_cleanup is not None and now < self._next_chat_cleanup:
            return
        try:
            await self._events.publish(emit_delete_old_chat_messages())
        except Exception:
            logger.exception("Не удалось опубликовать очистку старых сообщений")
            return
        self._next_chat_cleanup = now + timedelta(hours=1)

    async def _publish_batch_cleanup(self) -> None:
        from app.events.tasks import emit_delete_old_word_add_batches

        now = datetime.now(timezone.utc)
        if self._next_batch_cleanup is not None and now < self._next_batch_cleanup:
            return
        try:
            await self._events.publish(emit_delete_old_word_add_batches())
        except Exception:
            logger.exception("Не удалось опубликовать очистку старых списков слов")
            return
        self._next_batch_cleanup = now + timedelta(hours=1)

    async def dispatch_due(self) -> None:
        from app.events.tasks import emit_schedule

        try:
            due = await self._claim_due()
        except Exception:
            logger.exception("Не удалось захватить просроченные запуски")
            return

        for user_telegram_id, version in due:
            token = log_user_id.set(user_telegram_id)
            try:
                await self._events.publish(emit_schedule(user_telegram_id, version))
            except Exception:
                logger.exception(
                    "Не удалось опубликовать событие расписания для пользователя %s",
                    user_telegram_id,
                )
            finally:
                log_user_id.reset(token)

    async def _claim_due(self) -> list[tuple[int, int]]:
        now = datetime.now(timezone.utc)
        async with self._transaction():
            users = await self._users.lock_due(now)
            due = [(user.telegram_user_id, user.version) for user in users]
            for user in users:
                user.next_run_at = now + self._lease
            return due
