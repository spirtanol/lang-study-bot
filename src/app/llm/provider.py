from collections.abc import Sequence
from typing import Protocol, TypeVar

from pydantic import BaseModel

from .types import LLMMessage


ResponseT = TypeVar("ResponseT", bound=BaseModel)


class LLMProvider(Protocol):
    async def generate_structured(
        self,
        messages: Sequence[LLMMessage],
        response_model: type[ResponseT],
    ) -> ResponseT:
        """Generate and validate a structured response."""
        ...
