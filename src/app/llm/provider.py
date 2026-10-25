from collections.abc import Sequence
from typing import Protocol, TypeVar

from langchain_core.tools import BaseTool
from pydantic import BaseModel

from .types import LLMMessage, LLMToolCall


ResponseT = TypeVar("ResponseT", bound=BaseModel)


class LLMProvider(Protocol):
    async def generate_structured(
        self,
        messages: Sequence[LLMMessage],
        response_model: type[ResponseT],
    ) -> ResponseT:
        """Generate and validate a structured response."""
        ...

    async def select_tool(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[BaseTool],
    ) -> list[LLMToolCall]:
        """Bind tools and return every call the model made."""
        ...
