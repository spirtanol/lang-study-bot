from collections.abc import Callable, Sequence

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.core.db import AsyncSession
from app.defs import StudySessionStatus
from app.models import StudySession

from .exceptions import ActiveStudySessionAlreadyExistsError


ACTIVE_SESSION_STATUSES = (
    StudySessionStatus.PENDING,
    StudySessionStatus.IN_PROGRESS,
    StudySessionStatus.DEFERRED,
    StudySessionStatus.DEFERRED_2,
)


class StudySessionRepository:
    def __init__(self, get_session: Callable[[], AsyncSession]):
        self._get_session = get_session

    async def get_latest_active(
        self,
        user_id: int,
        statuses: Sequence[StudySessionStatus] = ACTIVE_SESSION_STATUSES,
    ) -> StudySession | None:
        statement = (
            select(StudySession)
            .where(
                StudySession.user_id == user_id,
                StudySession.status.in_(statuses),
            )
            .order_by(
                StudySession.created_at.desc(),
                StudySession.id.desc(),
            )
            .limit(1)
        )
        return await self._get_session().scalar(statement)

    async def interrupt(self, session_id: int) -> None:
        await self._get_session().execute(
            update(StudySession)
            .where(
                StudySession.id == session_id,
                StudySession.status.in_(ACTIVE_SESSION_STATUSES),
            )
            .values(status=StudySessionStatus.INTERRUPTED)
        )

    async def complete(self, session_id: int) -> None:
        await self._get_session().execute(
            update(StudySession)
            .where(
                StudySession.id == session_id,
                StudySession.status == StudySessionStatus.IN_PROGRESS,
            )
            .values(status=StudySessionStatus.COMPLETED)
        )

    async def save(self, study_session: StudySession) -> StudySession:
        statement = (
            insert(StudySession)
            .values(
                user_id=study_session.user_id,
                status=study_session.status,
            )
            .on_conflict_do_nothing(
                index_elements=[StudySession.user_id],
                index_where=StudySession.status.in_(ACTIVE_SESSION_STATUSES),
            )
            .returning(StudySession)
        )
        saved_session = await self._get_session().scalar(statement)
        if saved_session is None:
            raise ActiveStudySessionAlreadyExistsError
        return saved_session
