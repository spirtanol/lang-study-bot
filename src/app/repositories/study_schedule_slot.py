from collections.abc import Callable, Sequence
from datetime import time

from sqlalchemy import and_, delete, exists, or_, select

from app.core.db import AsyncSession
from app.models import StudyScheduleSlot


class StudyScheduleSlotRepository:
    def __init__(self, get_session: Callable[[], AsyncSession]):
        self._get_session = get_session

    async def exists_between(
        self,
        user_id: int,
        start_time: time,
        end_time: time,
    ) -> bool:
        statement = select(
            exists().where(
                StudyScheduleSlot.user_id == user_id,
                _between(start_time, end_time),
            )
        )
        return bool(await self._get_session().scalar(statement))

    async def add(self, slot: StudyScheduleSlot) -> StudyScheduleSlot:
        session = self._get_session()
        session.add(slot)
        await session.flush()
        return slot

    async def list_for_user(self, user_id: int) -> Sequence[StudyScheduleSlot]:
        statement = (
            select(StudyScheduleSlot)
            .where(StudyScheduleSlot.user_id == user_id)
            .order_by(
                StudyScheduleSlot.local_time,
                StudyScheduleSlot.id,
            )
        )
        return list(await self._get_session().scalars(statement))

    async def delete(self, user_id: int, slot_id: int) -> bool:
        result = await self._get_session().execute(
            delete(StudyScheduleSlot).where(
                StudyScheduleSlot.user_id == user_id,
                StudyScheduleSlot.id == slot_id,
            )
        )
        return result.rowcount > 0

    async def delete_for_user(self, user_id: int) -> None:
        await self._get_session().execute(
            delete(StudyScheduleSlot).where(StudyScheduleSlot.user_id == user_id)
        )


def _between(start_time: time, end_time: time):
    if start_time <= end_time:
        return and_(
            StudyScheduleSlot.local_time >= start_time,
            StudyScheduleSlot.local_time <= end_time,
        )
    return or_(
        StudyScheduleSlot.local_time >= start_time,
        StudyScheduleSlot.local_time <= end_time,
    )
