from collections.abc import Callable
from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert

from app.core.db import AsyncSession
from app.models import TelegramUpdate

from .exceptions import TelegramUpdateAlreadyExistsError


class TelegramUpdateRepository:
    def __init__(self, get_session: Callable[[], AsyncSession]):
        self._get_session = get_session

    async def add(self, update_id: int) -> TelegramUpdate:
        statement = (
            insert(TelegramUpdate)
            .values(update_id=update_id)
            .on_conflict_do_nothing(index_elements=[TelegramUpdate.update_id])
            .returning(TelegramUpdate)
        )
        saved = await self._get_session().scalar(statement)
        if saved is None:
            raise TelegramUpdateAlreadyExistsError
        return saved

    async def delete_older_than(self, cutoff: datetime) -> None:
        await self._get_session().execute(
            delete(TelegramUpdate).where(TelegramUpdate.created_at < cutoff)
        )
