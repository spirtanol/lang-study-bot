from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


type LLMRole = Literal["system", "user", "assistant"]


class LLMMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: LLMRole
    content: str


class LLMToolCall(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    args: dict[str, Any]
