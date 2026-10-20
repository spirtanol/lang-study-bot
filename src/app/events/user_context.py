import logging
from contextvars import ContextVar, Token

from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult

from app.core.logging import user_telegram_id


logger = logging.getLogger("app.task")

_user_token: ContextVar[Token[int | None] | None] = ContextVar(
    "user_telegram_id_token",
    default=None,
)

_USER_KEYS = ("user_id", "user_telegram_id", "chat_id")


class UserContextMiddleware(TaskiqMiddleware):
    async def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        for key in _USER_KEYS:
            value = message.kwargs.get(key)
            if isinstance(value, int):
                _user_token.set(user_telegram_id.set(value))
                break
        return message

    async def post_execute(
        self,
        message: TaskiqMessage,
        result: TaskiqResult,
    ) -> None:
        _reset_user()

    async def on_error(
        self,
        message: TaskiqMessage,
        result: TaskiqResult,
        exception: BaseException,
    ) -> None:
        logger.exception("Задача %s", message.task_name, exc_info=exception)
        _reset_user()


def _reset_user() -> None:
    token = _user_token.get()
    if token is None:
        return
    user_telegram_id.reset(token)
    _user_token.set(None)
