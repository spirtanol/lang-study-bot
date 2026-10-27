from collections.abc import Callable, Sequence
from datetime import datetime, timedelta

from sqlalchemy import func, literal, or_, select, update
from sqlalchemy.dialects.postgresql import insert

from app.core.db import AsyncSession
from app.models import User

from .exceptions import UserAlreadyExistsError


class UserRepository:
    def __init__(self, get_session: Callable[[], AsyncSession]):
        self._get_session = get_session

    async def save(self, user: User) -> User:
        session = self._get_session()
        session.add(user)
        await session.flush()
        return user

    async def create(self, user: User) -> User:
        statement = (
            insert(User)
            .values(
                telegram_user_id=user.telegram_user_id,
                status=user.status,
                timezone=user.timezone,
            )
            .on_conflict_do_nothing(index_elements=[User.telegram_user_id])
            .returning(User)
        )
        saved = await self._get_session().scalar(statement)
        if saved is None:
            raise UserAlreadyExistsError
        return saved

    async def get_by_id(self, user_id: int) -> User | None:
        session = self._get_session()
        return await session.get(User, user_id)

    async def set_next_run_at(
        self,
        user_id: int,
        version: int,
        next_run_at: datetime | None,
    ) -> bool:
        result = await self._get_session().execute(
            update(User)
            .where(
                User.telegram_user_id == user_id,
                User.version == version,
            )
            .values(
                next_run_at=next_run_at,
                updated_at=func.now(),
            )
        )
        return result.rowcount > 0

    async def bump_version(self, user_id: int, version: int) -> bool:
        result = await self._get_session().execute(
            update(User)
            .where(
                User.telegram_user_id == user_id,
                User.version == version,
            )
            .values(
                version=User.version + 1,
                updated_at=func.now(),
            )
        )
        return result.rowcount > 0

    async def acquire_lock(
        self,
        user_id: int,
        version: int,
        lease: timedelta,
    ) -> User | None:
        statement = (
            update(User)
            .where(
                User.telegram_user_id == user_id,
                User.version == version,
                or_(
                    User.locked_at.is_(None),
                    User.locked_at < func.now() - literal(lease),
                ),
            )
            .values(locked_at=func.now())
            .returning(User)
        )
        return await self._get_session().scalar(statement)

    async def release_lock(self, user_id: int, locked_at: datetime) -> None:
        await self._get_session().execute(
            update(User)
            .where(
                User.telegram_user_id == user_id,
                User.locked_at == locked_at,
            )
            .values(locked_at=None)
        )

    async def lock_due(self, now: datetime) -> Sequence[User]:
        statement = (
            select(User)
            .where(User.next_run_at < now)
            .order_by(User.next_run_at)
            .with_for_update(skip_locked=True)
        )
        return (await self._get_session().scalars(statement)).all()
