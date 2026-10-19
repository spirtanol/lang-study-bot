from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.telegram.command import TELEGRAM_COMMANDS_CAPTIONS, TelegramCommand
from app.telegram.message import TelegramMessage
from app.telegram.texts import WELCOME_TEXT

CANCEL_MARKUP = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=TELEGRAM_COMMANDS_CAPTIONS[TelegramCommand.CANCEL],
                callback_data=TelegramCommand.CANCEL,
            ),
        ],
    ],
)
QUESTION_REPLY_MARKUP = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=TELEGRAM_COMMANDS_CAPTIONS[TelegramCommand.DONT_KNOW],
                callback_data=TelegramCommand.DONT_KNOW,
            ),
        ],
        [
            InlineKeyboardButton(
                text=TELEGRAM_COMMANDS_CAPTIONS[TelegramCommand.FINISH],
                callback_data=TelegramCommand.FINISH,
            ),
        ],
    ],
)
ADD_WORDS_MARKUP = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Пополнить",
                callback_data=TelegramCommand.ADD_WORDS,
            ),
        ],
    ],
)
STUDY_TIME_MARKUP = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Начать",
                callback_data=TelegramCommand.STUDY,
            ),
        ],
        [
            InlineKeyboardButton(
                text="В другой раз",
                callback_data=TelegramCommand.FINISH,
            ),
        ],
    ],
)
WELCOME = TelegramMessage(
    text=WELCOME_TEXT,
    reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ок", callback_data="ok")],
        ],
    ),
)
