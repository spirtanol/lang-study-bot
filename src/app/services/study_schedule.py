from collections.abc import Callable, Sequence
from contextlib import AbstractAsyncContextManager
from datetime import time

from app.models import StudyScheduleSlot
from app.repositories import StudyScheduleSlotRepository, UserRepository

from .exceptions import ScheduleSlotNotFoundError, ScheduleSlotTooCloseError
from .user import UserService

_MINUTES_IN_DAY = 24 * 60


class StudyScheduleService:
    def __init__(
        self,
        repository: StudyScheduleSlotRepository,
        users: UserRepository,
        user_service: UserService,
        transaction: Callable[[], AbstractAsyncContextManager[None]],
        slot_gap_minutes: int,
    ):
        self._repository = repository
        self._users = users
        self._user_service = user_service
        self._transaction = transaction
        self._slot_gap_minutes = slot_gap_minutes

    async def add_slot(
        self,
        user_id: int,
        local_time: time,
    ) -> StudyScheduleSlot:
        start_time, end_time = _window(local_time, self._slot_gap_minutes)
        async with self._transaction():
            await self._users.lock_user(user_id)
            if await self._repository.exists_between(
                user_id,
                start_time,
                end_time,
            ):
                raise ScheduleSlotTooCloseError
            slot = await self._repository.add(
                StudyScheduleSlot(
                    user_id=user_id,
                    local_time=local_time,
                )
            )
            await self._user_service.refresh_next_run(user_id)
            return slot

    async def get_schedule(self, user_id: int) -> Sequence[StudyScheduleSlot]:
        async with self._transaction():
            return await self._repository.list_for_user(user_id)

    async def delete_slot(self, user_id: int, slot_id: int) -> None:
        async with self._transaction():
            await self._users.lock_user(user_id)
            deleted = await self._repository.delete(user_id, slot_id)
            if not deleted:
                raise ScheduleSlotNotFoundError
            await self._user_service.refresh_next_run(user_id)

    async def clear(self, user_id: int) -> None:
        async with self._transaction():
            await self._users.lock_user(user_id)
            await self._repository.delete_for_user(user_id)
            await self._user_service.refresh_next_run(user_id)

    async def set_daily(
        self,
        user_id: int,
        local_time: time,
    ) -> Sequence[StudyScheduleSlot]:
        async with self._transaction():
            await self._users.lock_user(user_id)
            await self._repository.delete_for_user(user_id)
            slot = await self._repository.add(
                StudyScheduleSlot(
                    user_id=user_id,
                    local_time=local_time,
                )
            )
            await self._user_service.refresh_next_run(user_id)
            return [slot]


def _window(local_time: time, gap_minutes: int) -> tuple[time, time]:
    if 2 * gap_minutes >= _MINUTES_IN_DAY:
        return time.min, time.max
    minute = local_time.hour * 60 + local_time.minute
    return _clock(minute - gap_minutes), _clock(minute + gap_minutes)


def _clock(total_minutes: int) -> time:
    minute = total_minutes % _MINUTES_IN_DAY
    return time(hour=minute // 60, minute=minute % 60)
