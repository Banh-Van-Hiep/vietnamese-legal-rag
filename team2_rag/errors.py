from __future__ import annotations

import json
from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, ValidationError

from team2_rag.config.settings import ConfigError
from team2_rag.llm.errors import LLMError
from team2_rag.prompts.context import ContextBudgetError, ContextBuildError
from team2_rag.reranker import RerankModelError

try:  # jsonschema is already required by api.app; stay importable without it.
    from jsonschema import ValidationError as _SchemaValidationError

    SCHEMA_VALIDATION_ERRORS: tuple[type[BaseException], ...] = (_SchemaValidationError,)
except ImportError:  # pragma: no cover
    SCHEMA_VALIDATION_ERRORS = ()

try:  # Team 1 package; optional so this module stays importable (and testable) without it.
    from team1_data.retrieval.errors import RetrievalUnavailableError

    RETRIEVAL_ERRORS: tuple[type[BaseException], ...] = (RetrievalUnavailableError, RerankModelError)
except ImportError:  # pragma: no cover
    RetrievalUnavailableError = None
    RETRIEVAL_ERRORS = (RerankModelError,)


class ErrorCode(str, Enum):
    """Public codes, exactly as in the HTTP error-code reference table (Team 2 subset)."""

    INVALID_REQUEST = "INVALID_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UPSTREAM_INVALID_RESPONSE = "UPSTREAM_INVALID_RESPONSE"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    UPSTREAM_TIMEOUT = "UPSTREAM_TIMEOUT"


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: ErrorCode
    message: str
    retryable: bool


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    error: ErrorDetail


ERROR_SPECS: dict[ErrorCode, tuple[int, str, bool]] = {
    ErrorCode.INVALID_REQUEST: (400, "Yêu cầu không hợp lệ.", False),
    ErrorCode.NOT_FOUND: (404, "Không tìm thấy tài nguyên.", False),
    ErrorCode.METHOD_NOT_ALLOWED: (405, "Phương thức HTTP không được hỗ trợ.", False),
    ErrorCode.PAYLOAD_TOO_LARGE: (413, "Nội dung yêu cầu quá lớn.", False),
    ErrorCode.UNSUPPORTED_MEDIA_TYPE: (415, "Yêu cầu phải dùng JSON.", False),
    ErrorCode.INTERNAL_ERROR: (500, "Lỗi hệ thống nội bộ.", False),
    ErrorCode.UPSTREAM_INVALID_RESPONSE: (502, "Phản hồi từ dịch vụ xử lý không hợp lệ.", False),
    ErrorCode.SERVICE_UNAVAILABLE: (503, "Dịch vụ xử lý tạm thời không khả dụng.", True),
    ErrorCode.UPSTREAM_TIMEOUT: (504, "Dịch vụ tạm thời không phản hồi.", True),
}

# LLMError.error_code stays the internal VLRA-29 vocabulary (answer.to_error_response and its tests rely on it);
# it is translated to the public code only here.
_LLM_PUBLIC_CODES: dict[str, ErrorCode] = {
    "LLM_TIMEOUT": ErrorCode.UPSTREAM_TIMEOUT,
    "LLM_UNAVAILABLE": ErrorCode.SERVICE_UNAVAILABLE,
    "INVALID_LLM_OUTPUT": ErrorCode.UPSTREAM_INVALID_RESPONSE,
    "CITATION_INVALID": ErrorCode.UPSTREAM_INVALID_RESPONSE,
}

_HTTP_STATUS_CODES: dict[int, ErrorCode] = {
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.METHOD_NOT_ALLOWED,
    413: ErrorCode.PAYLOAD_TOO_LARGE,
    415: ErrorCode.UNSUPPORTED_MEDIA_TYPE,
    502: ErrorCode.UPSTREAM_INVALID_RESPONSE,
    503: ErrorCode.SERVICE_UNAVAILABLE,
    504: ErrorCode.UPSTREAM_TIMEOUT,
}


class Team2Error(Exception):
    code: ClassVar[ErrorCode] = ErrorCode.INTERNAL_ERROR

    def __init__(self, detail: str = "") -> None:
        super().__init__(detail)
        self.detail = detail


class InvalidRequestError(Team2Error):
    code = ErrorCode.INVALID_REQUEST


class InternalError(Team2Error):
    code = ErrorCode.INTERNAL_ERROR


def classify(exc: BaseException) -> ErrorCode:
    if isinstance(exc, Team2Error):
        return exc.code
    if isinstance(exc, LLMError):
        public = _LLM_PUBLIC_CODES.get(exc.error_code)
        if public is not None:
            return public
        try:
            return ErrorCode(exc.error_code)
        except ValueError:
            return ErrorCode.SERVICE_UNAVAILABLE
    if isinstance(exc, ConfigError):  # missing/invalid LLM configuration: service not ready, not a client error
        return ErrorCode.SERVICE_UNAVAILABLE
    if RetrievalUnavailableError is not None and isinstance(exc, RetrievalUnavailableError):
        return ErrorCode.UPSTREAM_TIMEOUT if isinstance(exc.__cause__, TimeoutError) else ErrorCode.SERVICE_UNAVAILABLE
    if isinstance(exc, RerankModelError):
        return ErrorCode.SERVICE_UNAVAILABLE
    if isinstance(exc, (ContextBuildError, ContextBudgetError)):
        return ErrorCode.INTERNAL_ERROR
    if isinstance(exc, SCHEMA_VALIDATION_ERRORS) or isinstance(exc, ValidationError):
        return ErrorCode.UPSTREAM_INVALID_RESPONSE  # generated response violates the response contract
    # Only a plain ValueError (input validation such as pipeline.validate_input) or a malformed-body decode error
    # is the client's fault. Specific ValueError subclasses (RerankInputError, PromptBuildError, ...) signal
    # internal contract violations and fall through to INTERNAL_ERROR.
    if type(exc) is ValueError or isinstance(exc, (json.JSONDecodeError, UnicodeError)):
        return ErrorCode.INVALID_REQUEST
    return ErrorCode.INTERNAL_ERROR


def classify_http_status(status_code: int) -> ErrorCode:
    """Public code for a framework-raised HTTPException (unknown route, wrong method, ...)."""
    code = _HTTP_STATUS_CODES.get(status_code)
    if code is not None:
        return code
    return ErrorCode.INVALID_REQUEST if 400 <= status_code < 500 else ErrorCode.INTERNAL_ERROR


def build_error_response(code: ErrorCode) -> tuple[int, ErrorResponse]:
    status, message, retryable = ERROR_SPECS[code]
    return status, ErrorResponse(error=ErrorDetail(code=code, message=message, retryable=retryable))
