import json
import logging
import logging.config
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any


user_telegram_id: ContextVar[int | None] = ContextVar(
    "user_telegram_id",
    default=None,
)


class UserContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        user_id = user_telegram_id.get()
        if user_id is not None:
            record.user_telegram_id = user_id
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "time": datetime.fromtimestamp(
                record.created,
                timezone.utc,
            ).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        user_id = getattr(record, "user_telegram_id", None)
        if user_id is not None:
            payload["user_telegram_id"] = user_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def logging_dict() -> dict[str, Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "user_context": {
                "()": "app.core.logging.UserContextFilter",
            },
        },
        "formatters": {
            "json": {
                "()": "app.core.logging.JsonFormatter",
            },
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "json",
                "filters": ["user_context"],
            },
        },
        "root": {
            "handlers": ["stdout"],
            "level": "INFO",
        },
        "loggers": {
            "sqlalchemy.engine": {
                "level": "WARNING",
            },
            "uvicorn.access": {
                "level": "WARNING",
            },
        },
    }


def init_logging() -> None:
    logging.config.dictConfig(logging_dict())
