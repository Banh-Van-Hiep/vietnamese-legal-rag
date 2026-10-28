from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from team2_rag.config.settings import ConfigError
from team2_rag.errors import (
    RETRIEVAL_ERRORS,
    SCHEMA_VALIDATION_ERRORS,
    ErrorCode,
    Team2Error,
    build_error_response,
    classify,
    classify_http_status,
)
from team2_rag.llm.errors import LLMError

logger = logging.getLogger("team2_rag.api")


def resolve_request_id(request: Request) -> str:
    """Request ID đã chốt cho request này; nếu chưa có: dùng X-Request-ID hợp lệ của client, không thì tạo mới."""
    known = getattr(request.state, "request_id", None)
    if known:
        return known
    incoming = request.headers.get("x-request-id", "")
    rid = incoming if 0 < len(incoming) <= 128 and incoming.isascii() and incoming.isprintable() else str(uuid4())
    request.state.request_id = rid
    return rid


def internal_error_payload(code: ErrorCode, exc: BaseException | None = None) -> tuple[int, dict]:
    """Keep the existing error table; translate only the Python -> Java wire code (spec 9.14)."""
    status, response = build_error_response(code)
    body = response.model_dump(mode="json")
    wire_code = {
        "UPSTREAM_INVALID_RESPONSE": "INVALID_LLM_OUTPUT",
        "SERVICE_UNAVAILABLE": "LLM_UNAVAILABLE",
        "UPSTREAM_TIMEOUT": "LLM_TIMEOUT",
    }.get(code.value, code.value)
    if isinstance(exc, LLMError) and exc.error_code in {
        "INVALID_LLM_OUTPUT", "CITATION_INVALID", "LLM_UNAVAILABLE", "LLM_TIMEOUT",
    }:
        wire_code = exc.error_code
    elif isinstance(exc, RETRIEVAL_ERRORS):
        wire_code = "RETRIEVAL_TIMEOUT" if status == 504 else "RETRIEVAL_UNAVAILABLE"
    body["error"]["code"] = wire_code
    return status, body


def _respond(request: Request, code: ErrorCode, exc: BaseException, headers: dict | None = None) -> JSONResponse:
    request_id = resolve_request_id(request)
    headers = {**(headers or {}), "X-Request-ID": request_id}
    status, body = internal_error_payload(code, exc)
    if status >= 500:
        logger.error("request_failed request_id=%s code=%s exc=%s", request_id, body["error"]["code"], type(exc).__name__)
    else:
        logger.warning("request_rejected request_id=%s code=%s exc=%s", request_id, body["error"]["code"], type(exc).__name__)
    return JSONResponse(status_code=status, content=body, headers=headers)


async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
    return _respond(request, classify(exc), exc)


async def handle_request_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _respond(request, ErrorCode.INVALID_REQUEST, exc)


async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Unknown route (404), wrong method (405, keeps the Allow header), 413/415 raised by the framework or handlers.
    # The framework's `detail` is deliberately not echoed.
    return _respond(request, classify_http_status(exc.status_code), exc, headers=getattr(exc, "headers", None))


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, handle_request_validation)
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(Team2Error, handle_exception)
    app.add_exception_handler(LLMError, handle_exception)
    app.add_exception_handler(ValidationError, handle_exception)
    app.add_exception_handler(ConfigError, handle_exception)
    for retrieval_error in RETRIEVAL_ERRORS:
        app.add_exception_handler(retrieval_error, handle_exception)
    for schema_error in SCHEMA_VALIDATION_ERRORS:
        app.add_exception_handler(schema_error, handle_exception)
    app.add_exception_handler(ValueError, handle_exception)
    app.add_exception_handler(Exception, handle_exception)
