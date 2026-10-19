from sqlalchemy import Enum as SAEnum, ForeignKey, Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.defs import StudyAttemptStatus

from .base import (
    BaseModel,
    IdMixin,
    TimestampMixin,
    enum_check_constraint,
)


class StudyAttempt(IdMixin, TimestampMixin, BaseModel):
    __tablename__ = "study_attempts"
    __table_args__ = (
        enum_check_constraint(
            "status",
            StudyAttemptStatus,
            "ck_study_attempts_status",
        ),
        Index(
            "uq_study_attempts_session_vocabulary_item",
            "session_id",
            "vocabulary_item_id",
            unique=True,
        ),
        Index(
            "uq_study_attempts_pending_session",
            "session_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("study_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    vocabulary_item_id: Mapped[int] = mapped_column(
        ForeignKey("vocabulary_items.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[StudyAttemptStatus] = mapped_column(
        SAEnum(
            StudyAttemptStatus,
            name="ck_study_attempts_status",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda items: [item.value for item in items],
            length=16,
        ),
        nullable=False,
        default=StudyAttemptStatus.PENDING,
        server_default=StudyAttemptStatus.PENDING.value,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
