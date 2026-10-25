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
    InternalErrorCode,
    Team2Error,
    build_internal_error_response,
    classify_internal,
    classify_internal_http_status,
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


def _respond(request: Request, code: InternalErrorCode, exc: BaseException, headers: dict | None = None) -> JSONResponse:
    request_id = resolve_request_id(request)
    headers = {**(headers or {}), "X-Request-ID": request_id}
    status, body = build_internal_error_response(code)
    if status >= 500:
        # NFR-13: exception text/tracebacks may contain prompts, answers or credentials.
        logger.error("request_failed request_id=%s code=%s exc=%s", request_id, code.value, type(exc).__name__)
    else:
        logger.warning("request_rejected request_id=%s code=%s exc=%s", request_id, code.value, type(exc).__name__)
    return JSONResponse(status_code=status, content=body.model_dump(mode="json"), headers=headers)


async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
    return _respond(request, classify_internal(exc), exc)


async def handle_request_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _respond(request, InternalErrorCode.INVALID_REQUEST, exc)


async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Unknown route (404), wrong method (405, keeps the Allow header), 413/415 raised by the framework or handlers.
    # The framework's `detail` is deliberately not echoed.
    return _respond(request, classify_internal_http_status(exc.status_code), exc, headers=getattr(exc, "headers", None))


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
