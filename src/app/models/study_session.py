from sqlalchemy import Enum as SAEnum, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from app.defs import StudySessionStatus

from .base import (
    BaseModel,
    IdMixin,
    TimestampMixin,
    enum_check_constraint,
)


class StudySession(IdMixin, TimestampMixin, BaseModel):
    __tablename__ = "study_sessions"
    __table_args__ = (
        enum_check_constraint(
            "status",
            StudySessionStatus,
            "ck_study_sessions_status",
        ),
        Index(
            "uq_study_sessions_active_user",
            "user_id",
            unique=True,
            postgresql_where=text(
                "status IN ('pending', 'in_progress', 'deferred', 'deferred_2')"
            ),
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[StudySessionStatus] = mapped_column(
        SAEnum(
            StudySessionStatus,
            name="ck_study_sessions_status",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda items: [item.value for item in items],
            length=16,
        ),
        nullable=False,
        default=StudySessionStatus.PENDING,
        server_default=StudySessionStatus.PENDING.value,
        index=True,
    )
