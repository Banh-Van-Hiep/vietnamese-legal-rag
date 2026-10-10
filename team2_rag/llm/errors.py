"""Internal LLM errors mapped to the Team 2 I/O specification."""
from __future__ import annotations


class LLMError(Exception):
    retryable = False
    error_code = "LLM_UNAVAILABLE"

    def __init__(self, message: str, *, provider: str = "", status: int | None = None):
        super().__init__(message)
        self.provider = provider
        self.status = status


class LLMTimeoutError(LLMError):
    retryable = True
    error_code = "LLM_TIMEOUT"


class LLMRateLimitError(LLMError):
    retryable = True
    error_code = "LLM_UNAVAILABLE"


class LLMProviderError(LLMError):
    retryable = True
    error_code = "LLM_UNAVAILABLE"


class LLMAuthError(LLMError):
    error_code = "LLM_UNAVAILABLE"


class LLMConfigError(LLMError):
    error_code = "LLM_UNAVAILABLE"


class LLMContentBlockedError(LLMError):
    error_code = "LLM_UNAVAILABLE"


class LLMBadOutputError(LLMError):
    error_code = "INVALID_LLM_OUTPUT"

    def __init__(self, message: str, *, provider: str = "", raw_text: str = ""):
        super().__init__(message, provider=provider)
        self.raw_text = raw_text
