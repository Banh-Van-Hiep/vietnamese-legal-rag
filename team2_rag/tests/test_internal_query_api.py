"""Real `POST /internal/v1/query` through `create_app` with a fake pipeline (no models, no network, no API key).

pytest-style (needs: pytest, fastapi, httpx, pydantic, jsonschema). Run: python -m pytest team2_rag/tests -q
Covers HTTP mapping, internal error bodies, request-id propagation and response validation of the REAL app wiring.
It does not prove retrieval/rerank/LLM quality; those are faked.
"""
import json
import logging
import threading
import uuid

import pytest

pytest.importorskip("httpx")
pytest.importorskip("jsonschema")
pytest.importorskip("pydantic")

from fastapi.testclient import TestClient  # noqa: E402

from team2_rag.api import create_app  # noqa: E402
from team2_rag.api.app import BODY_LIMIT, ROOT  # noqa: E402
from team2_rag.config.settings import ConfigError  # noqa: E402
from team2_rag.llm.errors import (  # noqa: E402
    CitationInvalidError, LLMAuthError, LLMBadOutputError, LLMProviderError, LLMRateLimitError, LLMTimeoutError,
)
from team2_rag.models.response import RAGResponse  # noqa: E402
from team2_rag.prompts.context import ContextBudgetError, ContextBuildError  # noqa: E402
from team2_rag.reranker import RerankInputError, RerankModelError  # noqa: E402
from team2_rag.tests.helpers import citation  # noqa: E402

URL = "/internal/v1/query"
SECRET = "sk-very-secret-raw-provider-error"
VALID = {"question": "Luật Doanh nghiệp quy định về những vấn đề gì?", "history": []}
INTERNAL_CODES = {"INVALID_REQUEST", "NOT_FOUND", "METHOD_NOT_ALLOWED", "PAYLOAD_TOO_LARGE", "UNSUPPORTED_MEDIA_TYPE",
                "INTERNAL_ERROR", "INVALID_LLM_OUTPUT", "CITATION_INVALID", "LLM_UNAVAILABLE", "LLM_TIMEOUT",
                "RETRIEVAL_UNAVAILABLE", "RETRIEVAL_TIMEOUT"}


def good():
    return {"status": "answered", "answer": "Nội dung quy định [C1].", "citations": [citation("C1", "chunk-a")]}


class FakePipeline:
    def __init__(self, result=None, exc=None, started=None, release=None):
        self.result, self.exc, self.started, self.release = result if result is not None else good(), exc, started, release
        self.calls = []

    def query(self, question, history, request_id=None):
        self.calls.append((question, history, request_id))
        if self.started:
            self.started.set()
        if self.release:
            self.release.wait(10)
        if self.exc:
            raise self.exc
        return self.result


def make(pipe=None, **kw):
    if not (ROOT / "contracts" / "v0.1" / "rag_response.schema.json").is_file():
        pytest.skip("contracts/v0.1/rag_response.schema.json not present in this checkout")
    return create_app(pipe or FakePipeline(), **kw)


def client(app):
    return TestClient(app, raise_server_exceptions=False)


def post(c, body, headers=None, url=URL):
    content = body if isinstance(body, (bytes, str)) else json.dumps(body, ensure_ascii=False)
    h = {"content-type": "application/json", **(headers or {})}
    return c.post(url, content=content.encode("utf-8") if isinstance(content, str) else content, headers=h)


def assert_error(r, status, code, retryable):
    assert r.status_code == status, r.text
    body = r.json()
    assert set(body) == {"error"} and set(body["error"]) == {"code", "message", "retryable"}
    assert body["error"]["code"] == code and code in INTERNAL_CODES
    assert body["error"]["retryable"] is retryable
    assert r.headers.get("x-request-id")                      # present on errors, not only on success
    assert SECRET not in r.text and "Traceback" not in r.text


# ---------------------------------------------------------------- success path
def test_success_returns_contract_body_and_echoes_request_id():
    pipe = FakePipeline()
    with client(make(pipe)) as c:
        r = post(c, {"question": "  Luật Doanh nghiệp?  ", "history": []}, {"X-Request-ID": "req-123"})
    assert r.status_code == 200 and r.headers["x-request-id"] == "req-123"
    assert r.json() == good()
    RAGResponse.model_validate(r.json())
    assert pipe.calls == [("Luật Doanh nghiệp?", [], "req-123")]


def test_request_id_generated_when_missing_or_invalid():
    with client(make()) as c:
        missing = post(c, VALID)
        too_long = post(c, VALID, {"X-Request-ID": "x" * 129})
    for r in (missing, too_long):
        assert r.status_code == 200 and str(uuid.UUID(r.headers["x-request-id"]))
    assert missing.headers["x-request-id"] != too_long.headers["x-request-id"]


def test_insufficient_context_is_a_success_response():
    out = {"status": "insufficient_context", "answer": "Chưa đủ căn cứ.", "citations": []}
    with client(make(FakePipeline(out))) as c:
        r = post(c, VALID)
    assert r.status_code == 200 and r.json() == out


# ---------------------------------------------------------------- request validation
def test_unsupported_media_type():
    with client(make()) as c:
        r = c.post(URL, content=b"{}", headers={"content-type": "text/plain", "X-Request-ID": "rid-1"})
    assert_error(r, 415, "UNSUPPORTED_MEDIA_TYPE", False)
    assert r.headers["x-request-id"] == "rid-1"


def test_json_content_type_with_charset_is_accepted():
    with client(make()) as c:
        r = post(c, VALID, {"content-type": "application/json; charset=utf-8"})
    assert r.status_code == 200


def test_query_string_rejected():
    pipe = FakePipeline()
    with client(make(pipe)) as c:
        r = post(c, VALID, url=URL + "?debug=1")
    assert_error(r, 400, "INVALID_REQUEST", False)
    assert pipe.calls == []


def test_oversized_body_rejected_before_parsing():
    pipe = FakePipeline()
    big = '{"question":"a","history":[],"pad":"' + "a" * (BODY_LIMIT + 10) + '"}'
    with client(make(pipe)) as c:
        r = post(c, big)
    assert_error(r, 413, "PAYLOAD_TOO_LARGE", False)
    assert pipe.calls == []


@pytest.mark.parametrize("raw", [
    "not json", "[]", "null", '{"question":"a"}', '{"history":[]}', '{"question":"a","history":[],"extra":1}',
    '{"question":"","history":[]}', '{"question":"   ","history":[]}', '{"question":1,"history":[]}',
    '{"question":"a","history":null}', '{"question":"a","history":"x"}',
    '{"question":"a","history":[{"role":"user","content":"x"}]}',
    '{"question":"a","history":[{"role":"assistant","content":"x"},{"role":"user","content":"y"}]}',
    '{"question":"a","history":[{"role":"user","content":"x","extra":1},{"role":"assistant","content":"y"}]}',
    '{"question":"a","question":"b","history":[]}', '{"question":NaN,"history":[]}',
    json.dumps({"question": "q" * 2001, "history": []}),
    json.dumps({"question": "a", "history": [{"role": r, "content": "x"} for r in ["user", "assistant"] * 6]}),
])
def test_invalid_bodies_are_400_and_never_reach_the_pipeline(raw):
    pipe = FakePipeline()
    with client(make(pipe)) as c:
        r = post(c, raw)
    assert_error(r, 400, "INVALID_REQUEST", False)
    assert pipe.calls == []


def test_invalid_utf8_body_is_400():
    with client(make()) as c:
        assert_error(post(c, b"\xff\xfe"), 400, "INVALID_REQUEST", False)


# ---------------------------------------------------------------- routing
def test_get_on_query_is_405_with_allow_header_and_public_body():
    with client(make()) as c:
        r = c.get(URL)
    assert_error(r, 405, "METHOD_NOT_ALLOWED", False)
    assert "POST" in r.headers.get("allow", "")


def test_public_backend_route_is_not_served_by_the_internal_service():
    with client(make()) as c:
        r = post(c, VALID, url="/api/v1/query")
    assert_error(r, 404, "NOT_FOUND", False)


def test_health_and_ready():
    with client(make()) as c:
        assert c.get("/internal/v1/health").json() == {"status": "up"}
        assert c.get("/internal/v1/ready").json() == {"status": "ready"}


# ---------------------------------------------------------------- startup failure, busy, timeout
def test_startup_failure_keeps_service_up_but_unavailable_and_is_diagnosable(caplog):
    def broken():
        raise ConfigError("LLM_MODEL chưa được cấu hình.")
    with caplog.at_level(logging.ERROR), client(make(runtime_factory=broken)) as c:
        assert c.get("/internal/v1/health").status_code == 200
        assert_error(c.get("/internal/v1/ready"), 503, "LLM_UNAVAILABLE", True)
        assert_error(post(c, VALID), 503, "LLM_UNAVAILABLE", True)
    assert any("rag_startup_failed" in r.getMessage() and "ConfigError" in r.getMessage() for r in caplog.records)
    assert "LLM_MODEL" not in caplog.text


def test_non_config_startup_failure_does_not_log_exception_text(caplog):
    def broken():
        raise RuntimeError(SECRET)
    with caplog.at_level(logging.ERROR), client(make(runtime_factory=broken)) as c:
        assert_error(post(c, VALID), 503, "LLM_UNAVAILABLE", True)
    assert "rag_startup_failed" in caplog.text and SECRET not in caplog.text


def test_runtime_is_closed_on_shutdown():
    closed = []

    class Runtime:
        pipeline = FakePipeline()
        def close(self): closed.append(True)
    with client(make(runtime_factory=Runtime)) as c:
        assert post(c, VALID).status_code == 200
    assert closed == [True]


def test_busy_service_returns_503_then_recovers():
    started, release = threading.Event(), threading.Event()
    app = make(FakePipeline(started=started, release=release))
    first = {}
    with client(app) as c1, client(app) as c2:
        t = threading.Thread(target=lambda: first.setdefault("r", post(c1, VALID)))
        t.start()
        assert started.wait(5)
        assert_error(post(c2, VALID), 503, "LLM_UNAVAILABLE", True)
        release.set()
        t.join(10)
        assert first["r"].status_code == 200
        assert post(c2, VALID).status_code == 200


def test_timeout_is_504_and_slot_stays_held_until_work_finishes():
    started, release = threading.Event(), threading.Event()
    app = make(FakePipeline(started=started, release=release), timeout_seconds=0.05)
    with client(app) as c:
        assert_error(post(c, VALID), 504, "LLM_TIMEOUT", True)
        assert started.wait(2)
        assert_error(post(c, VALID), 503, "LLM_UNAVAILABLE", True)   # no pile-up of abandoned inferences
        release.set()


def test_app_factory_argument_validation():
    for bad in (0, -1, 46):
        with pytest.raises(ValueError):
            make(timeout_seconds=bad)
    with pytest.raises(TypeError):
        make(response_model=object)


# ---------------------------------------------------------------- exception mapping through the REAL endpoint
RAISED = [
    (lambda: LLMTimeoutError(SECRET, provider="openai"), 504, "LLM_TIMEOUT", True),
    (lambda: LLMRateLimitError(SECRET), 503, "LLM_UNAVAILABLE", True),
    (lambda: LLMProviderError(SECRET), 503, "LLM_UNAVAILABLE", True),
    (lambda: LLMAuthError(SECRET), 503, "LLM_UNAVAILABLE", True),
    (lambda: LLMBadOutputError(SECRET, raw_text=SECRET), 502, "INVALID_LLM_OUTPUT", False),
    (lambda: CitationInvalidError(SECRET), 502, "CITATION_INVALID", False),
    (lambda: ConfigError(SECRET), 503, "LLM_UNAVAILABLE", True),
    (lambda: RerankModelError(SECRET), 503, "RETRIEVAL_UNAVAILABLE", True),
    (lambda: RerankInputError(SECRET), 500, "INTERNAL_ERROR", False),
    (lambda: ContextBuildError(SECRET), 500, "INTERNAL_ERROR", False),
    (lambda: ContextBudgetError(SECRET), 500, "INTERNAL_ERROR", False),
    (lambda: ValueError(SECRET), 400, "INVALID_REQUEST", False),
    (lambda: RuntimeError(SECRET), 500, "INTERNAL_ERROR", False),
]


@pytest.mark.parametrize("make_exc,status,code,retryable", RAISED)
def test_pipeline_exceptions_map_to_public_errors_with_request_id(make_exc, status, code, retryable):
    with client(make(FakePipeline(exc=make_exc()))) as c:
        r = post(c, VALID, {"X-Request-ID": "rid-err"})
    assert_error(r, status, code, retryable)
    assert r.headers["x-request-id"] == "rid-err"


def test_retrieval_errors_map_to_503_and_504():
    mod = pytest.importorskip("team1_data.retrieval.errors")
    for cause, status, code in ((None, 503, "RETRIEVAL_UNAVAILABLE"), (TimeoutError(), 504, "RETRIEVAL_TIMEOUT")):
        exc = mod.RetrievalUnavailableError.__new__(mod.RetrievalUnavailableError)   # avoid Team 1 constructor
        exc.__cause__ = cause
        with client(make(FakePipeline(exc=exc))) as c:
            assert_error(post(c, VALID), status, code, True)


@pytest.mark.parametrize("bad", [
    {"status": "answered", "answer": "Không có marker.", "citations": [citation("C1", "chunk-a")]},
    {**good(), "unexpected": 1},
    {"status": "unknown", "answer": "A", "citations": []},
    {"status": "answered", "answer": "A [C2] [C1].", "citations": [citation("C1", "chunk-a"), citation("C2", "chunk-b")]},
    {"status": "answered", "answer": "A [C1].", "citations": [{**citation("C1", "chunk-a"), "source_url": "http://x.vn/a"}]},
    ["not", "an", "object"],
])
def test_invalid_generated_output_is_502_not_200(bad):
    with client(make(FakePipeline(bad))) as c:
        assert_error(post(c, VALID), 502, "INVALID_LLM_OUTPUT", False)


# ---------------------------------------------------------------- Pydantic model vs JSON Schema must not drift
def test_pydantic_model_and_json_schema_agree_on_core_contract():
    from jsonschema import Draft202012Validator, FormatChecker
    schema = json.loads((ROOT / "contracts" / "v0.1" / "rag_response.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    ok = [good(), {"status": "insufficient_context", "answer": "Chưa đủ căn cứ.", "citations": []}]
    bad = [{**good(), "extra": 1}, {**good(), "status": "unknown"}, {"status": "answered", "answer": "A [C1]."}]
    for payload in ok:
        validator.validate(payload)
        RAGResponse.model_validate(payload)
    for payload in bad:
        assert not validator.is_valid(payload)
        with pytest.raises(Exception):
            RAGResponse.model_validate(payload)
