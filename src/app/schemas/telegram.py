from abc import ABC
from typing import Literal, Self, cast

from aiogram.types import ReplyMarkupUnion
from pydantic import AliasPath, BaseModel, ConfigDict, Field, model_validator


class IncomingTelegramMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    user_id: int = Field(
        strict=True,
        validation_alias=AliasPath("from", "id"),
    )
    text: str = Field(min_length=1)


class TelegramCallbackQuery(BaseModel):
    model_config = ConfigDict(extra="ignore")

    user_id: int = Field(
        strict=True,
        validation_alias=AliasPath("from", "id"),
    )
    query_id: str = Field(min_length=1, validation_alias="id")
    data: str = Field(min_length=1)


class IncomingTelegramUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    update_id: int = Field(strict=True)
    message: IncomingTelegramMessage | None = None
    callback_query: TelegramCallbackQuery | None = None

    @model_validator(mode="after")
    def _one_source(self) -> Self:
        if (self.message is None) == (self.callback_query is None):
            raise ValueError("Нужно сообщение или callback")
        return self

    @property
    def user_id(self) -> int:
        if self.message is not None:
            return self.message.user_id
        return cast(TelegramCallbackQuery, self.callback_query).user_id

    @property
    def text(self) -> str:
        if self.message is not None:
            return self.message.text
        return cast(TelegramCallbackQuery, self.callback_query).data


class TelegramMethodResponse(BaseModel, ABC):
    method: str


class AnswerCallbackQueryResponse(TelegramMethodResponse):
    method: Literal["answerCallbackQuery"] = "answerCallbackQuery"
    callback_query_id: str = Field(min_length=1)


class SendMessageResponse(TelegramMethodResponse):
    method: Literal["sendMessage"] = "sendMessage"
    chat_id: int = Field(strict=True)
    text: str
    reply_markup: ReplyMarkupUnion | None = None