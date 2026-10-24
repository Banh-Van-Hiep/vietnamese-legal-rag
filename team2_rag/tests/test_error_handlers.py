import pytest

pytest.importorskip("httpx")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from team2_rag.api.handlers import install_error_handlers
from team2_rag.errors import (
    ERROR_SPECS,
    ErrorCode,
    InternalError,
    InvalidRequestError,
    build_error_response,
    classify,
)
from team2_rag.llm.errors import (
    CitationInvalidError,
    LLMAuthError,
    LLMBadOutputError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from team2_rag.prompts.context import ContextBudgetError, ContextBuildError

SECRET = "sk-very-secret-raw-provider-error"

CASES = {
    "timeout": (lambda: LLMTimeoutError(SECRET, provider="openai"), 504, "LLM_TIMEOUT", True),
    "rate": (lambda: LLMRateLimitError(SECRET), 503, "LLM_UNAVAILABLE", True),
    "provider": (lambda: LLMProviderError(SECRET), 503, "LLM_UNAVAILABLE", True),
    "auth": (lambda: LLMAuthError(SECRET), 503, "LLM_UNAVAILABLE", True),
    "bad_output": (lambda: LLMBadOutputError(SECRET, raw_text=SECRET), 502, "INVALID_LLM_OUTPUT", False),
    "citation": (lambda: CitationInvalidError(SECRET), 502, "CITATION_INVALID", False),
    "invalid_req": (lambda: InvalidRequestError(SECRET), 400, "INVALID_REQUEST", False),
    "value": (lambda: ValueError(SECRET), 400, "INVALID_REQUEST", False),
    "ctx_build": (lambda: ContextBuildError(SECRET), 500, "INTERNAL_ERROR", False),
    "ctx_budget": (lambda: ContextBudgetError(SECRET), 500, "INTERNAL_ERROR", False),
    "internal": (lambda: InternalError(SECRET), 500, "INTERNAL_ERROR", False),
    "unhandled": (lambda: RuntimeError(SECRET), 500, "INTERNAL_ERROR", False),
}


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/raise/{kind}")
    def raise_(kind: str):
        raise CASES[kind][0]()

    @app.get("/int")
    def int_(x: int):
        return {"x": x}

    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("kind", list(CASES))
def test_exception_to_standard_json(client, kind):
    _, status, code, retryable = CASES[kind]
    r = client.get(f"/raise/{kind}")
    assert r.status_code == status
    body = r.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message", "retryable"}
    assert body["error"]["code"] == code
    assert body["error"]["retryable"] is retryable
    assert SECRET not in r.text


def test_request_validation_error_is_400(client):
    r = client.get("/int", params={"x": "abc"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"
    assert set(r.json()) == {"error"}


def test_every_error_code_has_spec_and_builds_response():
    for code in ErrorCode:
        status, body = build_error_response(code)
        assert status == ERROR_SPECS[code][0]
        assert body.error.code is code


def test_classify_unknown_llm_code_falls_back_to_unavailable():
    exc = LLMProviderError("x")
    exc.error_code = "SOMETHING_NEW"
    assert classify(exc) is ErrorCode.LLM_UNAVAILABLE
