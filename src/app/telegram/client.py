from functools import lru_cache

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.types import BotCommand, ReplyMarkupUnion

from app.core.disposer import reg_to_dispose

from .command import TELEGRAM_COMMAND_DESCRIPTIONS, TelegramCommand


@lru_cache
def _get_http_session(api_uri: str) -> AiohttpSession:
    session = AiohttpSession(
        api=TelegramAPIServer.from_base(api_uri),
    )
    reg_to_dispose(session.close)
    return session


class TelegramClient:
    def __init__(self, token: str, api_uri: str) -> None:
        self._bot = Bot(
            token=token,
            session=_get_http_session(api_uri),
        )

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: ReplyMarkupUnion | None = None,
    ) -> None:
        await self._bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
        )

    async def set_commands(self) -> None:
        await self._bot.set_my_commands(
            [
                BotCommand(
                    command=command.value,
                    description=TELEGRAM_COMMAND_DESCRIPTIONS[command],
                )
                for command in TelegramCommand
            ]
        )

    async def set_webhook(self, url: str, secret_token: str) -> None:
        await self._bot.set_webhook(url=url, secret_token=secret_token)

    async def delete_webhook(self) -> None:
        await self._bot.delete_webhook()
