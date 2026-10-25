import json

import pytest

pytest.importorskip("httpx")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from team2_rag.api.handlers import install_error_handlers
from team2_rag.config.settings import ConfigError
from team2_rag.errors import (
    ERROR_SPECS,
    ErrorCode,
    InternalErrorCode,
    InternalError,
    InvalidRequestError,
    build_error_response,
    classify,
    classify_http_status,
    build_internal_error_response,
)
from team2_rag.llm.errors import (
    CitationInvalidError,
    LLMAuthError,
    LLMBadOutputError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from team2_rag.prompts.builder import PromptBuildError
from team2_rag.prompts.context import ContextBudgetError, ContextBuildError
from team2_rag.reranker import RerankInputError, RerankModelError

SECRET = "sk-very-secret-raw-provider-error"

# HTTP error-code reference table (Team 2 subset): public code -> (HTTP status, retryable).
REFERENCE = {
    "INVALID_REQUEST": (400, False),
    "NOT_FOUND": (404, False),
    "METHOD_NOT_ALLOWED": (405, False),
    "PAYLOAD_TOO_LARGE": (413, False),
    "UNSUPPORTED_MEDIA_TYPE": (415, False),
    "INTERNAL_ERROR": (500, False),
    "UPSTREAM_INVALID_RESPONSE": (502, False),
    "SERVICE_UNAVAILABLE": (503, True),
    "UPSTREAM_TIMEOUT": (504, True),
}

INTERNAL_REFERENCE = {
    "INVALID_REQUEST": (400, False), "NOT_FOUND": (404, False),
    "DOCUMENT_NOT_FOUND": (404, False), "ARTICLE_NOT_FOUND": (404, False),
    "METHOD_NOT_ALLOWED": (405, False), "PAYLOAD_TOO_LARGE": (413, False),
    "UNSUPPORTED_MEDIA_TYPE": (415, False), "INTERNAL_ERROR": (500, False),
    "INVALID_LLM_OUTPUT": (502, False), "CITATION_INVALID": (502, False),
    "LLM_UNAVAILABLE": (503, True), "RETRIEVAL_UNAVAILABLE": (503, True),
    "LLM_TIMEOUT": (504, True), "RETRIEVAL_TIMEOUT": (504, True),
}


try:
    from team1_data.retrieval.errors import RetrievalUnavailableError
except ImportError:  # pragma: no cover
    RetrievalUnavailableError = None


def _retrieval_error(cause=None):
    # __new__ avoids depending on Team 1's constructor signature.
    exc = RetrievalUnavailableError.__new__(RetrievalUnavailableError)
    exc.__cause__ = cause
    return exc


class _InternalValueError(ValueError):
    """Stand-in for an internal ValueError subclass that is not a client mistake."""


CASES = {
    "timeout": (lambda: LLMTimeoutError(SECRET, provider="openai"), 504, "LLM_TIMEOUT", True),
    "rate": (lambda: LLMRateLimitError(SECRET), 503, "LLM_UNAVAILABLE", True),
    "provider": (lambda: LLMProviderError(SECRET), 503, "LLM_UNAVAILABLE", True),
    "auth": (lambda: LLMAuthError(SECRET), 503, "LLM_UNAVAILABLE", True),
    "bad_output": (lambda: LLMBadOutputError(SECRET, raw_text=SECRET), 502, "INVALID_LLM_OUTPUT", False),
    "citation": (lambda: CitationInvalidError(SECRET), 502, "CITATION_INVALID", False),
    "invalid_req": (lambda: InvalidRequestError(SECRET), 400, "INVALID_REQUEST", False),
    "value": (lambda: ValueError(SECRET), 400, "INVALID_REQUEST", False),
    "json_decode": (lambda: json.JSONDecodeError(SECRET, "{}", 0), 400, "INVALID_REQUEST", False),
    "rerank_input": (lambda: RerankInputError(SECRET), 500, "INTERNAL_ERROR", False),
    "prompt_build": (lambda: PromptBuildError(SECRET), 500, "INTERNAL_ERROR", False),
    "value_subclass": (lambda: _InternalValueError(SECRET), 500, "INTERNAL_ERROR", False),
    "ctx_build": (lambda: ContextBuildError(SECRET), 500, "INTERNAL_ERROR", False),
    "ctx_budget": (lambda: ContextBudgetError(SECRET), 500, "INTERNAL_ERROR", False),
    "internal": (lambda: InternalError(SECRET), 500, "INTERNAL_ERROR", False),
    "unhandled": (lambda: RuntimeError(SECRET), 500, "INTERNAL_ERROR", False),
    "config": (lambda: ConfigError(SECRET), 503, "LLM_UNAVAILABLE", True),
    "rerank_model": (lambda: RerankModelError(SECRET), 503, "RETRIEVAL_UNAVAILABLE", True),
}
if RetrievalUnavailableError is not None:
    CASES["retrieval_down"] = (lambda: _retrieval_error(), 503, "RETRIEVAL_UNAVAILABLE", True)
    CASES["retrieval_timeout"] = (lambda: _retrieval_error(TimeoutError()), 504, "RETRIEVAL_TIMEOUT", True)

try:
    from jsonschema import ValidationError as SchemaValidationError
except ImportError:  # pragma: no cover
    SchemaValidationError = None
if SchemaValidationError is not None:
    CASES["schema"] = (lambda: SchemaValidationError(SECRET), 502, "INVALID_LLM_OUTPUT", False)

HTTP_CASES = [
    (400, "INVALID_REQUEST"), (401, "INVALID_REQUEST"), (404, "NOT_FOUND"), (405, "METHOD_NOT_ALLOWED"),
    (413, "PAYLOAD_TOO_LARGE"), (415, "UNSUPPORTED_MEDIA_TYPE"), (418, "INVALID_REQUEST"),
    (500, "INTERNAL_ERROR"), (502, "UPSTREAM_INVALID_RESPONSE"), (503, "SERVICE_UNAVAILABLE"),
    (504, "UPSTREAM_TIMEOUT"),
]
INTERNAL_HTTP_CASES = [
    (status, {"UPSTREAM_INVALID_RESPONSE": "INVALID_LLM_OUTPUT", "SERVICE_UNAVAILABLE": "LLM_UNAVAILABLE",
              "UPSTREAM_TIMEOUT": "LLM_TIMEOUT"}.get(code, code))
    for status, code in HTTP_CASES
]


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/raise/{kind}")
    def raise_(kind: str):
        raise CASES[kind][0]()

    @app.get("/http/{status}")
    def http_(status: int):
        raise StarletteHTTPException(status_code=status, detail=SECRET)

    @app.get("/int")
    def int_(x: int):
        return {"x": x}

    return TestClient(app, raise_server_exceptions=False)


def assert_error_body(r, status, code, retryable):
    assert r.status_code == status
    body = r.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message", "retryable"}
    assert body["error"]["code"] == code
    assert body["error"]["retryable"] is retryable
    assert SECRET not in r.text


@pytest.mark.parametrize("kind", list(CASES))
def test_exception_to_standard_json(client, kind):
    _, status, code, retryable = CASES[kind]
    assert_error_body(client.get(f"/raise/{kind}"), status, code, retryable)


@pytest.mark.parametrize("raised,code", INTERNAL_HTTP_CASES)
def test_http_exception_to_standard_json(client, raised, code):
    status, retryable = INTERNAL_REFERENCE[code]
    assert_error_body(client.get(f"/http/{raised}"), status, code, retryable)


def test_unknown_route_is_404_not_found(client):
    assert_error_body(client.get("/no-such-route"), 404, "NOT_FOUND", False)


def test_wrong_method_is_405_and_keeps_allow_header(client):
    r = client.post("/int")
    assert_error_body(r, 405, "METHOD_NOT_ALLOWED", False)
    assert "GET" in r.headers["allow"]


def test_request_validation_error_is_400(client):
    r = client.get("/int", params={"x": "abc"})
    assert_error_body(r, 400, "INVALID_REQUEST", False)


def test_error_specs_match_reference_table():
    assert {c.value for c in ErrorCode} == set(REFERENCE)
    for code in ErrorCode:
        status, _message, retryable = ERROR_SPECS[code]
        assert (status, retryable) == REFERENCE[code.value]


def test_every_error_code_has_spec_and_builds_response():
    for code in ErrorCode:
        status, body = build_error_response(code)
        assert status == ERROR_SPECS[code][0]
        assert body.error.code is code


def test_internal_vocabulary_matches_the_python_to_java_contract():
    assert {c.value for c in InternalErrorCode} == set(INTERNAL_REFERENCE)
    for code in InternalErrorCode:
        status, body = build_internal_error_response(code)
        assert (status, body.error.retryable) == INTERNAL_REFERENCE[code.value]
        assert body.error.code.value == code.value


def test_failure_log_keeps_trace_and_type_without_raw_exception(client, caplog):
    with caplog.at_level("ERROR", logger="team2_rag.api"):
        response = client.get("/raise/provider", headers={"X-Request-ID": "safe-trace"})
    assert response.status_code == 503
    assert "safe-trace" in caplog.text and "LLMProviderError" in caplog.text
    assert SECRET not in caplog.text and "Traceback" not in caplog.text


def test_classify_unknown_llm_code_falls_back_to_service_unavailable():
    exc = LLMProviderError("x")
    exc.error_code = "SOMETHING_NEW"
    assert classify(exc) is ErrorCode.SERVICE_UNAVAILABLE


@pytest.mark.parametrize("status,code", [(s, c) for s, c in HTTP_CASES])
def test_classify_http_status(status, code):
    assert classify_http_status(status).value == code
