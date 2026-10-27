from collections.abc import Awaitable, Callable

from pydantic import ValidationError
from taskiq import AsyncTaskiqDecoratedTask, Context, TaskiqDepends

from app.events.broker import get_brokers
from app.events.tasks.free_text_tools import (
    add_words_tool,
    set_schedule_tool,
    set_timezone_tool,
    start_study_tool,
    translate_words_tool,
)
from app.events.tasks.telegram import emit_telegram
from app.llm import LLMError, LLMMessage, LLMUnavailableError
from app.services.exceptions import UserBusyError, UserVersionError
from app.telegram import TelegramMessage
from app.telegram.texts import (
    MODEL_UNAVAILABLE_TEXT,
    TEXT_ACTION_FAILED_TEXT,
    TEXT_TOO_LONG_TEXT,
)

TEXT_ACTION_SYSTEM_PROMPT = (
    "Choose at most one tool for the user message. "
    "Call translate_words when the user asks to translate "
    "or sends English words or short phrases without asking to add them. "
    "Call add_words when the user asks to add words to the dictionary "
    "and the message contains those words. "
    "Pass only the words or short phrases, not the command. "
    "Do not call translate_words for that message. "
    "Call start_study when the user asks to start a lesson. "
    "Call set_timezone when the user asks to set or change "
    "their time zone and the message contains a city, "
    "a time zone name, or a UTC offset. "
    "Pass only that value, not the whole sentence. "
    "Call set_schedule when the user asks to set or change "
    "their lesson schedule and the message contains a clock time. "
    "Pass only that time, not the whole sentence. "
    "If none fits, do not call a tool."
)


async def _handle(
    user_id: int,
    version: int,
    text: str,
    context: Context = TaskiqDepends(),
) -> None:
    container = context.state.container

    async def publish(message: TelegramMessage) -> None:
        await container.event_service.publish(emit_telegram(user_id, message))

    replies = container.user_reply_service
    tools = [
        translate_words_tool(user_id, version, replies, publish),
        start_study_tool(user_id, version, replies, publish),
        set_timezone_tool(user_id, version, replies, publish),
        set_schedule_tool(user_id, version, replies, publish),
        add_words_tool(user_id, version, replies, publish),
    ]
    tools_by_name = {item.name: item for item in tools}
    try:
        async with container.user_service.lock(user_id, version):
            limit = container.config.input_max_length
            if len(text) > limit:
                await publish(
                    TelegramMessage(text=TEXT_TOO_LONG_TEXT.format(limit=limit)),
                )
                return

            try:
                calls = await container.language_model_service.select_tool(
                    (
                        LLMMessage(role="system", content=TEXT_ACTION_SYSTEM_PROMPT),
                        LLMMessage(role="user", content=text),
                    ),
                    tools,
                )
            except LLMUnavailableError:
                await publish(TelegramMessage(text=MODEL_UNAVAILABLE_TEXT))
                return
            except LLMError:
                await publish(TelegramMessage(text=TEXT_ACTION_FAILED_TEXT))
                return

            call = calls[0] if calls else None
            selected = None if call is None else tools_by_name.get(call.name)
            if call is None or selected is None:
                await publish(TelegramMessage(text=TEXT_ACTION_FAILED_TEXT))
                return
            try:
                await selected.ainvoke(call.args)
            except ValidationError:
                await publish(TelegramMessage(text=TEXT_ACTION_FAILED_TEXT))
                return
    except UserVersionError:
        return


_task: AsyncTaskiqDecoratedTask = get_brokers().common_broker.register_task(
    _handle,
    task_name="free_text",
    retry_on_error=True,
    max_retries=8,
    types_of_exceptions=(UserBusyError,),
)


def emit_free_text(
    user_id: int,
    version: int,
    text: str,
) -> Callable[[], Awaitable[None]]:
    async def emit() -> None:
        await _task.kiq(user_id=user_id, version=version, text=text)

    return emit
