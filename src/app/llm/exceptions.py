class LLMError(Exception):
    """Base exception for LLM provider failures."""


class LLMUnavailableError(LLMError):
    """The configured LLM provider is unavailable."""


class LLMTimeoutError(LLMUnavailableError):
    """The LLM provider did not respond before the timeout."""


class LLMResponseError(LLMError):
    """The provider returned an invalid or unparseable response."""


class LLMRateLimitError(LLMUnavailableError):
    """The provider rejected the request because the rate limit was reached."""


def is_rate_limited(error: BaseException) -> bool:
    if getattr(error, "code", None) == 429:
        return True
    response = getattr(error, "response", None)
    return getattr(response, "status_code", None) == 429
