from aiogram.types import ReplyMarkupUnion
from pydantic import BaseModel


class TelegramMessage(BaseModel):
    text: str
    reply_markup: ReplyMarkupUnion | None = None
