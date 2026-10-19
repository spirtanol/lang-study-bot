from collections.abc import Sequence
from typing import TypeVar

import httpx
from google.genai.errors import APIError
from langchain_core.exceptions import OutputParserException
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import (
    ChatGoogleGenerativeAIError,
    GoogleRateLimitError,
)
from pydantic import BaseModel, ValidationError

from .exceptions import (
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
    LLMUnavailableError,
    is_rate_limited,
)
from .messages import to_langchain_messages
from .types import LLMMessage


ResponseT = TypeVar("ResponseT", bound=BaseModel)


class GeminiProvider:
    def __init__(
        self,
        model: str,
        api_key: str,
        temperature: float,
        timeout_seconds: float,
    ):
        self._model = ChatGoogleGenerativeAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
            timeout=timeout_seconds,
            # 1 — один запрос без повторов SDK. 0 для этого клиента значит дефолт Google.
            max_retries=1,
        )

    async def generate_structured(
        self,
        messages: Sequence[LLMMessage],
        response_model: type[ResponseT],
    ) -> ResponseT:
        structured = self._model.with_structured_output(
            response_model,
            method="json_schema",
        )
        try:
            result = await structured.ainvoke(to_langchain_messages(messages))
        except (httpx.TimeoutException, TimeoutError) as error:
            raise LLMTimeoutError(str(error)) from error
        except (
            ConnectionError,
            httpx.HTTPError,
            APIError,
            ChatGoogleGenerativeAIError,
        ) as error:
            if isinstance(error, GoogleRateLimitError) or is_rate_limited(error):
                raise LLMRateLimitError(str(error)) from error
            raise LLMUnavailableError(str(error)) from error
        except (OutputParserException, ValidationError) as error:
            raise LLMResponseError(str(error)) from error

        if not isinstance(result, response_model):
            raise LLMResponseError("Модель вернула ответ неверной схемы")
        return result
