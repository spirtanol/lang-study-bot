from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.defs import StudySessionStatus, UserStatus
from app.models import StudyScheduleSlot, User
from app.repositories import (
    StudyAttemptRepository,
    StudyScheduleSlotRepository,
    StudySessionRepository,
    UserAlreadyExistsError,
    UserRepository,
)

from .exceptions import UserBusyError, UserVersionError

_DAY = timedelta(days=1)
_locked_users: ContextVar[tuple[User, ...]] = ContextVar(
    "locked_users",
    default=(),
)


@dataclass(frozen=True, slots=True)
class UserGetOrCreate:
    user: User
    created: bool


class UserService:
    DEFAULT_USER_ID = -1
    DEFAULT_TIMEZONE = "UTC"

    def __init__(
        self,
        repository: UserRepository,
        slots: StudyScheduleSlotRepository,
        sessions: StudySessionRepository,
        attempts: StudyAttemptRepository,
        transaction: Callable[[], AbstractAsyncContextManager[None]],
        session_timeout: timedelta,
        lock_lease: timedelta,
    ):
        self._repository = repository
        self._slots = slots
        self._sessions = sessions
        self._attempts = attempts
        self._transaction = transaction
        self._session_timeout = session_timeout
        self._lock_lease = lock_lease

    async def get_default_user(self) -> User:
        result = await self.get_or_create(self.DEFAULT_USER_ID)
        return result.user

    async def get_or_create(self, user_telegram_id: int) -> UserGetOrCreate:
        async with self._transaction():
            user = await self._repository.get_by_id(user_telegram_id)
            if user is not None:
                return UserGetOrCreate(user, created=False)

            user = User(
                telegram_user_id=user_telegram_id,
                status=UserStatus.ACTIVE,
                timezone=self.DEFAULT_TIMEZONE,
            )
            try:
                saved = await self._repository.create(user)
            except UserAlreadyExistsError:
                existing = await self._repository.get_by_id(user_telegram_id)
                if existing is None:
                    raise RuntimeError("Пользователь не сохранился и не найден")
                return UserGetOrCreate(existing, created=False)
            return UserGetOrCreate(saved, created=True)

    async def refresh_next_run(self, user_id: int) -> None:
        async with self._transaction():
            user = await self._repository.get_by_id(user_id)
            if user is None:
                return
            version = user.version
            session = await self._sessions.get_latest_active(
                user_id,
                (
                    StudySessionStatus.PENDING,
                    StudySessionStatus.IN_PROGRESS,
                    StudySessionStatus.DEFERRED,
                ),
            )
            if session is None:
                slots = await self._slots.list_for_user(user_id)
                next_run_at = _next_run_at(
                    slots,
                    user.timezone,
                    datetime.now(timezone.utc),
                )
            elif session.status == StudySessionStatus.PENDING:
                next_run_at = session.created_at + self._session_timeout
            elif session.status == StudySessionStatus.DEFERRED:
                next_run_at = session.updated_at + self._session_timeout
            else:
                attempt = await self._attempts.get_latest(session.id)
                anchor = (
                    attempt.updated_at
                    if attempt is not None
                    else session.updated_at
                )
                next_run_at = anchor + self._session_timeout
            saved = await self._repository.set_next_run_at(
                user_id,
                version,
                next_run_at,
            )
            if not saved:
                raise UserVersionError

    @asynccontextmanager
    async def lock(self, user_id: int, version: int) -> AsyncIterator[User]:
        held = _locked_users.get()
        locked = next(
            (user for user in held if user.telegram_user_id == user_id),
            None,
        )
        if locked is not None:
            yield locked
            return

        async with self._transaction():
            user = await self._repository.acquire_lock(
                user_id,
                version,
                self._lock_lease,
            )
            if user is None:
                current = await self._repository.get_by_id(user_id)
                if current is not None and current.version == version:
                    raise UserBusyError
                raise UserVersionError
            locked_at = user.locked_at
            if locked_at is None:
                raise RuntimeError("Аренда не записалась")
        token = _locked_users.set((*held, user))
        try:
            yield user
        finally:
            _locked_users.reset(token)
            async with self._transaction():
                await self._repository.release_lock(user_id, locked_at)


def _next_run_at(
    slots: Sequence[StudyScheduleSlot],
    timezone_name: str | None,
    now: datetime,
) -> datetime | None:
    if not slots:
        return None
    zone = ZoneInfo(timezone_name or UserService.DEFAULT_TIMEZONE)
    local_now = now.astimezone(zone)
    return min(
        _next_occurrence(local_now, slot.local_time) for slot in slots
    ).astimezone(timezone.utc)


def _next_occurrence(local_now: datetime, local_time: time) -> datetime:
    candidate = datetime.combine(
        local_now.date(),
        local_time.replace(tzinfo=None),
        tzinfo=local_now.tzinfo,
    )
    if candidate <= local_now:
        candidate += _DAY
    return candidate
