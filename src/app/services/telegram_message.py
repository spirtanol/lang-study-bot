import logging

from app.defs import MessageDirect
from app.services.chat_message import ChatMessageService
from app.telegram import TelegramClient, TelegramMessage


logger = logging.getLogger("app.telegram")


class TelegramMessageService:
    def __init__(self, client: TelegramClient, messages: ChatMessageService):
        self._client = client
        self._messages = messages

    async def send(self, chat_id: int, message: TelegramMessage) -> None:
        logger.info("%s", message.text)
        await self._client.send_message(
            chat_id,
            message.text,
            message.reply_markup,
        )
        await self._messages.add(chat_id, MessageDirect.OUT, message.text)
