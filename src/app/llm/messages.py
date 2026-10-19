from collections.abc import Sequence
from typing import assert_never

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from .types import LLMMessage


def to_langchain_messages(messages: Sequence[LLMMessage]) -> list[BaseMessage]:
    return [_to_langchain_message(message) for message in messages]


def _to_langchain_message(message: LLMMessage) -> BaseMessage:
    match message.role:
        case "system":
            return SystemMessage(content=message.content)
        case "user":
            return HumanMessage(content=message.content)
        case "assistant":
            return AIMessage(content=message.content)
        case _ as unexpected:
            assert_never(unexpected)
