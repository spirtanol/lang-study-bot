from collections.abc import Awaitable, Callable
from typing import Annotated

from langchain_core.tools import BaseTool, tool
from pydantic import Field

from app.services.user_reply import UserReplyService
from app.telegram import TelegramCommand, TelegramMessage
from app.telegram.reply import QUESTION_REPLY_MARKUP
from app.telegram.texts import QUESTION_TEXT


def translate_words_tool(
    user_id: int,
    version: int,
    replies: UserReplyService,
    publish: Callable[[TelegramMessage], Awaitable[None]],
) -> BaseTool:
    @tool
    async def translate_words(
        words: Annotated[
            str,
            Field(
                description=(
                    "English words or short phrases to translate, "
                    "separated by commas or line breaks."
                ),
            ),
        ],
    ) -> str:
        """Translate English words or short phrases into Russian."""
        message = await replies.handle_translate(user_id, version, words)
        if message is not None:
            await publish(message)
        return ""

    return translate_words


def start_study_tool(
    user_id: int,
    version: int,
    replies: UserReplyService,
    publish: Callable[[TelegramMessage], Awaitable[None]],
) -> BaseTool:
    @tool
    async def start_study() -> str:
        """Start a lesson when the user asks to begin studying."""
        message = await replies.handle_command(
            user_id,
            TelegramCommand.STUDY,
            version,
        )
        if message is not None:
            await publish(message)
        return ""

    return start_study


def set_timezone_tool(
    user_id: int,
    version: int,
    replies: UserReplyService,
    publish: Callable[[TelegramMessage], Awaitable[None]],
) -> BaseTool:
    @tool
    async def set_timezone(
        timezone: Annotated[
            str,
            Field(
                description=(
                    "City, IANA time zone, or UTC offset to set, "
                    "taken from the user message. "
                    "Examples: Moscow, Europe/Moscow, +3."
                ),
            ),
        ],
    ) -> str:
        """Set or change the user's time zone."""
        reply = await replies.handle_timezone(user_id, version, timezone)
        parts: list[str] = []
        reply_markup = None
        if reply.text:
            parts.append(reply.text)
        if reply.question is not None:
            parts.append(
                QUESTION_TEXT.format(
                    word=reply.question.word,
                    text=reply.question.text,
                ),
            )
            reply_markup = QUESTION_REPLY_MARKUP
        if parts:
            await publish(
                TelegramMessage(text="\n\n".join(parts), reply_markup=reply_markup),
            )
        return ""

    return set_timezone


def set_schedule_tool(
    user_id: int,
    version: int,
    replies: UserReplyService,
    publish: Callable[[TelegramMessage], Awaitable[None]],
) -> BaseTool:
    @tool
    async def set_schedule(
        time: Annotated[
            str,
            Field(
                description=(
                    "Clock time for the daily lesson, "
                    "taken from the user message. "
                    "Examples: 12:00, 09:30, в двенадцать."
                ),
            ),
        ],
    ) -> str:
        """Set or change the daily lesson time."""
        reply = await replies.handle_schedule(user_id, version, time)
        parts: list[str] = []
        reply_markup = None
        if reply.text:
            parts.append(reply.text)
        if reply.question is not None:
            parts.append(
                QUESTION_TEXT.format(
                    word=reply.question.word,
                    text=reply.question.text,
                ),
            )
            reply_markup = QUESTION_REPLY_MARKUP
        if parts:
            await publish(
                TelegramMessage(text="\n\n".join(parts), reply_markup=reply_markup),
            )
        return ""

    return set_schedule


def add_words_tool(
    user_id: int,
    version: int,
    replies: UserReplyService,
    publish: Callable[[TelegramMessage], Awaitable[None]],
) -> BaseTool:
    @tool
    async def add_words(
        words: Annotated[
            str,
            Field(
                description=(
                    "English words or short phrases to add, "
                    "separated by commas or line breaks. "
                    "Do not include the command. "
                    "«добавь слова apple, pear» gives «apple, pear»."
                ),
            ),
        ],
    ) -> str:
        """Add English words or short phrases to the user's dictionary."""
        reply = await replies.handle_add_words(user_id, version, words)
        parts: list[str] = []
        reply_markup = None
        if reply.text:
            parts.append(reply.text)
        if reply.question is not None:
            parts.append(
                QUESTION_TEXT.format(
                    word=reply.question.word,
                    text=reply.question.text,
                ),
            )
            reply_markup = QUESTION_REPLY_MARKUP
        if parts:
            await publish(
                TelegramMessage(text="\n\n".join(parts), reply_markup=reply_markup),
            )
        return ""

    return add_words
