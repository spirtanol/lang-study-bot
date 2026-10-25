from collections.abc import Sequence
from typing import TypeVar

import httpx
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama
from ollama import ResponseError
from pydantic import BaseModel, ValidationError

from .exceptions import (
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
    LLMUnavailableError,
    is_rate_limited,
    is_unavailable,
)
from .messages import to_langchain_messages
from .types import LLMMessage, LLMToolCall


ResponseT = TypeVar("ResponseT", bound=BaseModel)


class OllamaProvider:
    def __init__(
        self,
        model: str,
        base_url: str,
        temperature: float,
        context_size: int,
        timeout_seconds: float,
    ):
        self._model = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature,
            num_ctx=context_size,
            reasoning=False,
            client_kwargs={"timeout": timeout_seconds},
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
        except (ConnectionError, httpx.HTTPError) as error:
            if is_rate_limited(error):
                raise LLMRateLimitError(str(error)) from error
            raise LLMUnavailableError(str(error)) from error
        except (OutputParserException, ValidationError, ResponseError) as error:
            if is_unavailable(error):
                raise LLMUnavailableError(str(error)) from error
            raise LLMResponseError(str(error)) from error

        if not isinstance(result, response_model):
            raise LLMResponseError("Модель вернула ответ неверной схемы")
        return result

    async def select_tool(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[BaseTool],
    ) -> list[LLMToolCall]:
        bound = self._model.bind_tools(list(tools))
        try:
            result = await bound.ainvoke(to_langchain_messages(messages))
        except (httpx.TimeoutException, TimeoutError) as error:
            raise LLMTimeoutError(str(error)) from error
        except (ConnectionError, httpx.HTTPError) as error:
            if is_rate_limited(error):
                raise LLMRateLimitError(str(error)) from error
            raise LLMUnavailableError(str(error)) from error
        except (OutputParserException, ValidationError, ResponseError) as error:
            if is_unavailable(error):
                raise LLMUnavailableError(str(error)) from error
            raise LLMResponseError(str(error)) from error
        if not isinstance(result, AIMessage):
            raise LLMResponseError("Модель вернула ответ неверной схемы")
        calls: list[LLMToolCall] = []
        for call in result.tool_calls:
            name = call.get("name")
            args = call.get("args")
            if not isinstance(name, str) or name == "" or not isinstance(args, dict):
                raise LLMResponseError("Модель вернула вызов инструмента неверной схемы")
            calls.append(LLMToolCall(name=name, args=args))
        return calls
