from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import BigInteger, DateTime, Enum as SAEnum, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.defs import UserIntent, UserStatus

from .base import BaseModel, TimestampMixin, enum_check_constraint


class User(TimestampMixin, BaseModel):
    __tablename__ = "users"
    __table_args__ = (
        enum_check_constraint(
            "status",
            UserStatus,
            "ck_users_status",
        ),
        enum_check_constraint(
            "intent",
            UserIntent,
            "ck_users_intent",
        ),
        Index(
            "ix_users_next_run_at",
            "next_run_at",
            postgresql_where=text("next_run_at IS NOT NULL"),
        ),
        Index(
            "ix_users_telegram_user_id_version",
            "telegram_user_id",
            "version",
        ),
    )

    telegram_user_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        nullable=False,
    )
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(
            UserStatus,
            name="ck_users_status",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda items: [item.value for item in items],
            length=16,
        ),
        nullable=False,
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
    )
    intent: Mapped[UserIntent] = mapped_column(
        SAEnum(
            UserIntent,
            name="ck_users_intent",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda items: [item.value for item in items],
            length=16,
        ),
        nullable=False,
        default=UserIntent.UNKNOWN,
        server_default=UserIntent.UNKNOWN.value,
    )
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    def local_now(self) -> datetime:
        zone = ZoneInfo(self.timezone or "UTC")
        return datetime.now(zone)
