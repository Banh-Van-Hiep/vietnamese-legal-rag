"""VLRA-45: internal JSON API for Spring Boot; public chat/SSE stays Team 3's.

Run: python -m uvicorn team2_rag.api:create_app --factory --host 127.0.0.1 --port 8001
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from pydantic import ValidationError as ModelValidationError

from team1_data.retrieval.errors import RetrievalUnavailableError
from ..answer import to_error_response
from ..config.settings import ConfigError
from ..pipeline import validate_input, validate_generated_response
from ..reranker import RerankModelError
from ..runtime import build_runtime

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[2]
BODY_LIMIT = 256 * 1024


def _error(status, code, message, retryable=False, request_id=None):
    return JSONResponse({"error": {"code": code, "message": message, "retryable": retryable}},
                        status_code=status, headers={"X-Request-ID": request_id or str(uuid4())})


def _exception_response(exc, request_id):
    # Reuse Person 2's error body; only HTTP transport mapping belongs here.
    body = to_error_response(exc)
    if body is not None:
        status = {"LLM_TIMEOUT": 504, "LLM_UNAVAILABLE": 503,
                  "INVALID_LLM_OUTPUT": 502, "CITATION_INVALID": 502}[body["error"]["code"]]
        return JSONResponse(body, status_code=status, headers={"X-Request-ID": request_id})
    if isinstance(exc, RetrievalUnavailableError):
        timeout = isinstance(exc.__cause__, TimeoutError)
        return _error(504 if timeout else 503, "RETRIEVAL_TIMEOUT" if timeout else "RETRIEVAL_UNAVAILABLE",
                      "Dịch vụ truy xuất chưa phản hồi." if timeout else "Dịch vụ truy xuất chưa sẵn sàng.",
                      True, request_id)
    if isinstance(exc, (RerankModelError, ConfigError)):
        return _error(503, "SERVICE_UNAVAILABLE", "Dịch vụ xử lý chưa sẵn sàng.", True, request_id)
    # Do not emit provider messages, validation details, questions, or keys.
    log.error("rag_failed request_id=%s error_type=%s", request_id, type(exc).__name__)
    return _error(500, "INTERNAL_ERROR", "Không thể xử lý yêu cầu.", False, request_id)


def _pairs(pairs):
    obj = {}
    for k, value in pairs:
        if k in obj:
            raise ValueError("duplicate JSON field")
        obj[k] = value
    return obj


def create_app(pipeline=None, *, runtime_factory=build_runtime, timeout_seconds=45,
               error_installer=None, response_model=None):
    if not 0 < timeout_seconds <= 45:
        raise ValueError("timeout_seconds must be in (0, 45]")
    validator = Draft202012Validator(
        json.loads((ROOT / "contracts/v0.1/rag_response.schema.json").read_text(encoding="utf-8")),
        format_checker=FormatChecker(),
    )

    @asynccontextmanager
    async def lifespan(app):
        runtime = None
        app.state.pipeline = pipeline
        if pipeline is None:
            try:
                runtime = await asyncio.to_thread(runtime_factory)
                app.state.pipeline = runtime.pipeline
            except Exception as exc:
                log.error("rag_startup_failed error_type=%s", type(exc).__name__)
        yield
        if runtime is not None:
            runtime.close()

    app = FastAPI(title="Legal RAG internal service", version="0.1.0", lifespan=lifespan)
    # VLRA-47 is owned by Person 2 and has not been pushed at this baseline.
    # Use it automatically once present; never create a competing handlers.py.
    if error_installer is None:
        try:
            from .handlers import install_error_handlers
        except ModuleNotFoundError as exc:
            if exc.name != "team2_rag.api.handlers":
                raise
            log.warning("shared_error_handlers_pending task=VLRA-47")
        else:
            install_error_handlers(app)
            error_installer = install_error_handlers
    else:
        error_installer(app)
    # The shared Pydantic model can be injected without guessing its future
    # module path. TypedDict in types.py is NOT this validation model.
    if response_model is not None and not callable(getattr(response_model, "model_validate", None)):
        raise TypeError("response_model must be Person 2's validating RAGResponse model")
    # One inference at a time. A timed-out thread keeps its slot until it
    # really finishes, preventing repeated requests from accumulating work.
    slot = threading.Lock()

    @app.get("/internal/v1/health")
    def health():
        return {"status": "up"}

    @app.get("/internal/v1/ready")
    def ready():
        if getattr(app.state, "pipeline", None) is None:
            return _error(503, "SERVICE_UNAVAILABLE", "Dịch vụ chưa tải xong cấu hình hoặc mô hình.", True)
        return {"status": "ready"}

    @app.post("/internal/v1/query")
    async def query(request: Request):
        incoming = request.headers.get("x-request-id", "")
        request_id = incoming if 0 < len(incoming) <= 128 and incoming.isascii() and incoming.isprintable() else str(uuid4())
        request.state.request_id = request_id
        if request.url.query:
            return _error(400, "INVALID_REQUEST", "Không hỗ trợ query parameter.", request_id=request_id)
        if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
            return _error(415, "UNSUPPORTED_MEDIA_TYPE", "Yêu cầu phải dùng JSON.", request_id=request_id)
        raw = bytearray()
        async for block in request.stream():
            raw.extend(block)
            if len(raw) > BODY_LIMIT:
                return _error(413, "PAYLOAD_TOO_LARGE", "Nội dung yêu cầu quá lớn.", request_id=request_id)
        try:
            data = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
            if not isinstance(data, dict) or set(data) != {"question", "history"}:
                raise ValueError("expected exactly question and history")
            question, history = validate_input(data["question"], data["history"])
            if data["history"] is None:
                raise ValueError("history must be an array")
        except (UnicodeError, ValueError):
            return _error(400, "INVALID_REQUEST", "Câu hỏi hoặc lịch sử không hợp lệ.", request_id=request_id)
        active = getattr(app.state, "pipeline", None)
        if active is None or not slot.acquire(blocking=False):
            return _error(503, "SERVICE_UNAVAILABLE", "Dịch vụ chưa sẵn sàng hoặc đang bận.", True, request_id)

        def run():
            try:
                out = active.query(question, history, request_id=request_id)
                if response_model is None:
                    validator.validate(out)
                return validate_generated_response(out, response_model=response_model)
            finally:
                slot.release()

        work = asyncio.create_task(asyncio.to_thread(run))
        # Retrieve a late exception without leaking its contents into asyncio logs.
        work.add_done_callback(lambda task: None if task.cancelled() else task.exception())
        try:
            out = await asyncio.wait_for(asyncio.shield(work), timeout=timeout_seconds)
            return JSONResponse(out, headers={"X-Request-ID": request_id})
        except asyncio.TimeoutError:
            return _error(504, "UPSTREAM_TIMEOUT", "Dịch vụ xử lý chưa phản hồi trong thời hạn.", True, request_id)
        except (ValidationError, ModelValidationError):
            if error_installer is not None:
                raise
            return _error(502, "INVALID_LLM_OUTPUT", "Phản hồi từ dịch vụ xử lý không hợp lệ.", request_id=request_id)
        except Exception as exc:
            if error_installer is not None:
                raise
            return _exception_response(exc, request_id)

    return app
