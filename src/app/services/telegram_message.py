from app.telegram import TelegramClient, TelegramMessage


class TelegramMessageService:
    def __init__(self, client: TelegramClient):
        self._client = client

    async def send(self, chat_id: int, message: TelegramMessage) -> None:
        await self._client.send_message(
            chat_id,
            message.text,
            message.reply_markup,
        )
