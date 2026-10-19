from datetime import time

from sqlalchemy import ForeignKey, Time
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel, IdMixin, TimestampMixin


class StudyScheduleSlot(IdMixin, TimestampMixin, BaseModel):
    __tablename__ = "study_schedule_slots"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    local_time: Mapped[time] = mapped_column(Time, nullable=False)
