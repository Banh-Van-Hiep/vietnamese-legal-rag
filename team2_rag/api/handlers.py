from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from team2_rag.errors import ErrorCode, Team2Error, build_error_response, classify
from team2_rag.llm.errors import LLMError

logger = logging.getLogger("team2_rag.api")


def _respond(code: ErrorCode, exc: BaseException) -> JSONResponse:
    status, body = build_error_response(code)
    if status >= 500:
        logger.error("request_failed code=%s exc=%s", code.value, type(exc).__name__, exc_info=exc)
    else:
        logger.warning("request_rejected code=%s exc=%s", code.value, type(exc).__name__)
    return JSONResponse(status_code=status, content=body.model_dump(mode="json"))


async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
    return _respond(classify(exc), exc)


async def handle_request_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _respond(ErrorCode.INVALID_REQUEST, exc)


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, handle_request_validation)
    app.add_exception_handler(Team2Error, handle_exception)
    app.add_exception_handler(LLMError, handle_exception)
    app.add_exception_handler(ValidationError, handle_exception)
    app.add_exception_handler(ValueError, handle_exception)
    app.add_exception_handler(Exception, handle_exception)
