from typing import Literal

from pydantic import BaseModel, ConfigDict


type LLMRole = Literal["system", "user", "assistant"]


class LLMMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: LLMRole
    content: str
