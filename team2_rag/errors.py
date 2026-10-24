from __future__ import annotations

from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, ValidationError

from team2_rag.llm.errors import LLMError
from team2_rag.prompts.context import ContextBudgetError, ContextBuildError


class ErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    INVALID_LLM_OUTPUT = "INVALID_LLM_OUTPUT"
    CITATION_INVALID = "CITATION_INVALID"
    INTERNAL_ERROR = "INTERNAL_ERROR"


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
    ErrorCode.LLM_TIMEOUT: (504, "Dịch vụ tạm thời không phản hồi.", True),
    ErrorCode.LLM_UNAVAILABLE: (503, "Dịch vụ xử lý tạm thời không khả dụng.", True),
    ErrorCode.INVALID_LLM_OUTPUT: (502, "Phản hồi từ dịch vụ xử lý không hợp lệ.", False),
    ErrorCode.CITATION_INVALID: (502, "Phản hồi từ dịch vụ xử lý không hợp lệ.", False),
    ErrorCode.INTERNAL_ERROR: (500, "Lỗi hệ thống nội bộ.", False),
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
        try:
            return ErrorCode(exc.error_code)
        except ValueError:
            return ErrorCode.LLM_UNAVAILABLE
    if isinstance(exc, (ContextBuildError, ContextBudgetError)):
        return ErrorCode.INTERNAL_ERROR
    if isinstance(exc, ValidationError):
        return ErrorCode.INVALID_LLM_OUTPUT
    if isinstance(exc, ValueError):
        return ErrorCode.INVALID_REQUEST
    return ErrorCode.INTERNAL_ERROR


def build_error_response(code: ErrorCode) -> tuple[int, ErrorResponse]:
    status, message, retryable = ERROR_SPECS[code]
    return status, ErrorResponse(error=ErrorDetail(code=code, message=message, retryable=retryable))
