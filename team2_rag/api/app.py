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

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from jsonschema import Draft202012Validator, FormatChecker

from ..articles import ArticleResponse, JsonlArticleStore, validate_article_ids
from ..errors import ArticleStoreTimeoutError, InternalErrorCode, build_internal_error_response
from ..llm.errors import LLMBadOutputError
from ..models.response import RAGResponse
from ..pipeline import validate_input, validate_generated_response
from ..runtime import build_runtime
from .handlers import install_error_handlers, resolve_request_id

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[2]
BODY_LIMIT = 256 * 1024


def _error(code, request_id):
    """Early rejection using the same internal error vocabulary as exception handlers."""
    status, body = build_internal_error_response(code)
    log.log(logging.ERROR if status >= 500 else logging.WARNING,
            "rag_rejected request_id=%s code=%s http_status=%s", request_id, code.value, status)
    return JSONResponse(body.model_dump(mode="json"), status_code=status, headers={"X-Request-ID": request_id})


def _pairs(pairs):
    obj = {}
    for k, value in pairs:
        if k in obj:
            raise ValueError("duplicate JSON field")
        obj[k] = value
    return obj


def _close_runtime(runtime) -> None:
    """Best-effort close at shutdown/cleanup: never raises, never logs exception text (only its type)."""
    try:
        runtime.close()
    except Exception as exc:
        log.error("rag_shutdown_failed error_type=%s", type(exc).__name__)


def create_app(pipeline=None, *, runtime_factory=None, timeout_seconds=45,
               error_installer=None, response_model=None, article_store=None, article_timeout_seconds=10):
    """`response_model` defaults to the shared Pydantic `RAGResponse`; the JSON Schema stays the contract guard.

    Where the pipeline comes from:
    - neither argument: `build_runtime` runs at startup (the `--factory` uvicorn entry point);
    - `pipeline` only: it is served as-is and owned by the caller (the app never builds or closes anything);
    - `runtime_factory` given (with or without `pipeline`): the factory is authoritative. It runs at startup, its
      runtime is closed exactly once at shutdown, and if it fails the injected `pipeline` is NOT served, so a
      broken startup can never be masked by a stand-in (readiness 503, queries 503).
    """
    if not 0 < timeout_seconds <= 45:
        raise ValueError("timeout_seconds must be in (0, 45]")
    if not 0 < article_timeout_seconds <= 10:
        raise ValueError("article_timeout_seconds must be in (0, 10]")
    validator = Draft202012Validator(
        json.loads((ROOT / "contracts/v0.1/rag_response.schema.json").read_text(encoding="utf-8")),
        format_checker=FormatChecker(),
    )
    request_schema = json.loads(
        (ROOT / "contracts/v0.1/internal_query_request.schema.json").read_text(encoding="utf-8"))

    use_factory = runtime_factory is not None or pipeline is None
    factory = runtime_factory if runtime_factory is not None else build_runtime

    @asynccontextmanager
    async def lifespan(app):
        runtime = None
        # Reset on every startup so a previous run's state can never leak into this one.
        app.state.startup_error = None
        app.state.pipeline = None if use_factory else pipeline
        if use_factory:
            try:
                runtime = await asyncio.to_thread(factory)
                app.state.pipeline = runtime.pipeline
            except Exception as exc:
                log.error("rag_startup_failed error_type=%s", type(exc).__name__)
                app.state.startup_error = type(exc).__name__
                app.state.pipeline = None  # fail safe: /ready and /query answer 503, nothing half-initialised is served
                if runtime is not None:  # built but unusable (e.g. no pipeline): do not leak its resources
                    broken, runtime = runtime, None
                    _close_runtime(broken)
        served = app.state.pipeline if runtime is not None else None
        try:
            yield
        finally:
            if runtime is not None:
                owned, runtime = runtime, None  # cleared before closing: close runs at most once per runtime
                if app.state.pipeline is served:
                    app.state.pipeline = None  # nothing new may start on a closed runtime
                _close_runtime(owned)

    app = FastAPI(title="Legal RAG internal service", version="0.1.0", lifespan=lifespan)
    (error_installer or install_error_handlers)(app)
    if response_model is None:
        response_model = RAGResponse
    if not callable(getattr(response_model, "model_validate", None)):
        raise TypeError("response_model must be a Pydantic model with model_validate (default: RAGResponse)")
    # One inference at a time. A timed-out thread keeps its slot until it
    # really finishes, preventing repeated requests from accumulating work.
    slot = threading.Lock()
    source = article_store if article_store is not None else JsonlArticleStore.from_environment()

    @app.get("/internal/v1/health")
    def health():
        return {"status": "up"}

    @app.get("/internal/v1/ready")
    def ready(request: Request):
        if getattr(app.state, "pipeline", None) is None:
            return _error(InternalErrorCode.LLM_UNAVAILABLE, resolve_request_id(request))
        return {"status": "ready"}

    @app.get("/internal/v1/documents/{document_id}/articles/{article_id}", response_model=ArticleResponse)
    async def article(document_id: str, article_id: str, request: Request):
        request_id = resolve_request_id(request)
        if request.url.query:
            return _error(InternalErrorCode.INVALID_REQUEST, request_id)
        async for block in request.stream():
            if block:
                return _error(InternalErrorCode.INVALID_REQUEST, request_id)
        try:
            validate_article_ids(document_id, article_id)
        except ValueError:
            return _error(InternalErrorCode.INVALID_REQUEST, request_id)
        try:
            raw = await asyncio.wait_for(
                asyncio.to_thread(source.get_article, document_id, article_id), timeout=article_timeout_seconds)
        except asyncio.TimeoutError:
            raise ArticleStoreTimeoutError() from None
        result = ArticleResponse.model_validate(raw)
        if (result.document_id, result.article_id) != (document_id, article_id):
            raise LLMBadOutputError("Article response identity does not match the requested version")
        return JSONResponse(result.model_dump(mode="json"), headers={"X-Request-ID": request_id})

    @app.post("/internal/v1/query", response_model=RAGResponse, openapi_extra={
        "requestBody": {"required": True, "content": {"application/json": {"schema": request_schema}}},
    })
    async def query(request: Request):
        request_id = resolve_request_id(request)
        if request.url.query:
            return _error(InternalErrorCode.INVALID_REQUEST, request_id)
        if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
            return _error(InternalErrorCode.UNSUPPORTED_MEDIA_TYPE, request_id)
        raw = bytearray()
        async for block in request.stream():
            raw.extend(block)
            if len(raw) > BODY_LIMIT:
                return _error(InternalErrorCode.PAYLOAD_TOO_LARGE, request_id)
        try:
            data = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
            if not isinstance(data, dict) or set(data) != {"question", "history"}:
                raise ValueError("expected exactly question and history")
            question, history = validate_input(data["question"], data["history"])
            if data["history"] is None:
                raise ValueError("history must be an array")
        except (UnicodeError, ValueError):
            return _error(InternalErrorCode.INVALID_REQUEST, request_id)
        active = getattr(app.state, "pipeline", None)
        if active is None or not slot.acquire(blocking=False):
            return _error(InternalErrorCode.LLM_UNAVAILABLE, request_id)

        def run():
            try:
                out = active.query(question, history, request_id=request_id)
                validator.validate(out)  # JSON Schema = authoritative contract; RAGResponse adds marker/order checks.
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
            return _error(InternalErrorCode.LLM_TIMEOUT, request_id)
        # Every other exception propagates to the handlers installed above (internal error body with
        # X-Request-ID); nothing is swallowed or answered twice here.

    return app
