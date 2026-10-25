"""Regressions for spec v2.0 sections 7.6-7.8 and 9.8-9.14; no live AI claims."""
import copy
import json
import threading
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker
from pydantic import ValidationError

from team2_rag.answer import answer_from_rerank
from team2_rag.api import create_app
from team2_rag.api.app import ROOT
from team2_rag.api.mock_app import MOCK_ARTICLE, create_mock_app
from team2_rag.articles import JsonlArticleStore
from team2_rag.errors import ArticleStoreUnavailableError
from team2_rag.llm.errors import LLMBadOutputError
from team2_rag.llm.fake import FakeLLMProvider
from team2_rag.llm.service import LLMService
from team2_rag.mock import make_mock_response
from team2_rag.models.response import RAGResponse, validate_response_payload
from team2_rag.pipeline import RAGPipeline
from team2_rag.tests.test_rerank_to_answer import reply_for, retrieval_output


@pytest.mark.parametrize("marker", ["[C0]", "[C01]", "[c1]", "[ C1]", "[C1", "[C2\n"])
@pytest.mark.parametrize("status", ["answered", "insufficient_context"])
def test_shared_model_rejects_malformed_markers_on_its_own(marker, status):
    raw = make_mock_response(status)
    raw["answer"] += " " + marker
    with pytest.raises(ValidationError):
        RAGResponse.model_validate(raw)
    with pytest.raises(LLMBadOutputError):
        validate_response_payload(raw)


def test_shared_model_rejects_duplicate_source_chunks():
    raw = make_mock_response("answered")
    raw["answer"] += " [C2]."
    raw["citations"].append({**raw["citations"][0], "citation_id": "C2"})
    with pytest.raises(ValidationError):
        RAGResponse.model_validate(raw)


@pytest.mark.parametrize("question", ["Trường hợp vừa nêu thì sao?", "Công ty cổ phần là gì?"])
def test_direct_pipeline_validates_both_insufficient_exits(question):
    retriever = Mock()
    retriever.retrieve.return_value = {"question": question, "results": []}
    provider = FakeLLMProvider([])
    model = Mock()
    model.model_validate = Mock(wraps=RAGResponse.model_validate)
    pipeline = RAGPipeline(retriever, LLMService(provider), response_model=model)
    result = pipeline.query(question, [])
    assert result["status"] == "insufficient_context"
    model.model_validate.assert_called_once_with(result)
    assert provider.calls == []


@pytest.mark.parametrize("status", ["answered", "insufficient_context"])
def test_generation_entry_point_rejects_bad_markers_without_the_http_adapter(status):
    data = retrieval_output(1)
    raw = reply_for(data["results"], 0) if status == "answered" else {
        "status": status, "answer": "Chưa đủ căn cứ.", "citations": []}
    raw["answer"] += " [C0]"
    with pytest.raises(LLMBadOutputError):
        answer_from_rerank(data, LLMService(FakeLLMProvider([raw])))


def test_injected_model_cannot_weaken_the_response_contract():
    model = Mock()
    raw = make_mock_response("answered")
    raw["answer"] += " [C01]"
    model.model_validate.return_value.model_dump.return_value = raw
    with pytest.raises(LLMBadOutputError):
        validate_response_payload(raw, response_model=model)


def write_articles(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def test_viewer_reads_complete_articles_with_exact_version_and_no_llm(tmp_path):
    source = tmp_path / "articles.jsonl"
    original = {**MOCK_ARTICLE, "document_id": "fixture-v1", "article_id": "dieu-1",
                "content": "Điều 1\n1. Đoạn thứ nhất.\n2. Điều kiện và ngoại lệ đầy đủ.", "snapshot_id": "test"}
    later = {**original, "document_id": "fixture-v2", "content": "Nội dung phiên bản khác."}
    write_articles(source, [original, later])
    pipeline = Mock()
    app = create_app(pipeline, article_store=JsonlArticleStore(source))
    with TestClient(app) as client:
        response = client.get("/internal/v1/documents/fixture-v1/articles/dieu-1", headers={"X-Request-ID": "article-trace"})
        assert response.status_code == 200
        assert response.headers["x-request-id"] == "article-trace"
        assert response.json()["content"] == original["content"]
        assert response.json()["document_id"] == "fixture-v1"
        assert set(response.json()) == set(MOCK_ARTICLE)
        schema = json.loads((ROOT / "contracts/v0.1/internal_article.schema.json").read_text())
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(response.json())
        for doc, article, code in [("missing-v1", "dieu-1", "DOCUMENT_NOT_FOUND"),
                                   ("fixture-v1", "dieu-2", "ARTICLE_NOT_FOUND")]:
            missing = client.get(f"/internal/v1/documents/{doc}/articles/{article}")
            assert missing.status_code == 404 and missing.json()["error"]["code"] == code
        invalid = client.get("/internal/v1/documents/bad%20id/articles/dieu-1")
        assert invalid.status_code == 400
        assert client.get("/internal/v1/documents/fixture-v1/articles/dieu-1?extra=1").status_code == 400
    pipeline.query.assert_not_called()


def test_missing_article_store_does_not_fall_back_to_chunks_or_report_false_404(tmp_path):
    (tmp_path / "chunks.jsonl").write_text(json.dumps({"content": "This must never be used as a complete article."}))
    store = JsonlArticleStore(tmp_path / "articles.jsonl")
    with TestClient(create_app(Mock(), article_store=store)) as client:
        response = client.get("/internal/v1/documents/mock_v1/articles/art1")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "RETRIEVAL_UNAVAILABLE"
        write_articles(store.path, [MOCK_ARTICLE])
        assert client.get("/internal/v1/documents/mock_v1/articles/art1").status_code == 200


@pytest.mark.parametrize("rows", [[], [MOCK_ARTICLE, MOCK_ARTICLE], [{**MOCK_ARTICLE, "content": ""}]])
def test_corrupt_article_snapshot_is_unavailable(tmp_path, rows):
    path = tmp_path / "articles.jsonl"
    write_articles(path, rows)
    with pytest.raises(ArticleStoreUnavailableError):
        JsonlArticleStore(path).get_article("mock_v1", "art1")


def test_article_port_cannot_return_another_version():
    store = Mock()
    store.get_article.return_value = {**MOCK_ARTICLE, "document_id": "other-v2"}
    with TestClient(create_app(Mock(), article_store=store)) as client:
        response = client.get("/internal/v1/documents/mock_v1/articles/art1")
        assert response.status_code == 502
        assert response.json()["error"]["code"] == "INVALID_LLM_OUTPUT"


def test_article_timeout_uses_retrieval_timeout_code():
    release = threading.Event()
    store = Mock()
    store.get_article.side_effect = lambda *args: (release.wait(2), copy.deepcopy(MOCK_ARTICLE))[1]
    with TestClient(create_app(Mock(), article_store=store, article_timeout_seconds=.02)) as client:
        try:
            response = client.get("/internal/v1/documents/mock_v1/articles/art1")
            assert response.status_code == 504
            assert response.json()["error"]["code"] == "RETRIEVAL_TIMEOUT"
        finally:
            release.set()


@pytest.mark.parametrize("scenario", ["answered", "insufficient_context"])
def test_http_mock_runs_query_and_viewer_without_live_runtime(monkeypatch, scenario):
    monkeypatch.setenv("RAG_MOCK_SCENARIO", scenario)
    with patch("team2_rag.api.app.build_runtime", side_effect=AssertionError("must not load live runtime")) as build:
        with TestClient(create_mock_app()) as client:
            assert client.get("/internal/v1/ready").status_code == 200
            response = client.post("/internal/v1/query", json={"question": "Kiểm thử", "history": []})
            assert response.status_code == 200 and response.headers["x-rag-mode"] == "mock"
            assert response.json()["status"] == scenario
            RAGResponse.model_validate(response.json())
            for cited in response.json()["citations"]:
                article = client.get(f"/internal/v1/documents/{cited['document_id']}/articles/{cited['article_id']}")
                assert article.status_code == 200
                assert article.json()["source_url"] == cited["source_url"]
            rejected = client.post("/internal/v1/query", json={"question": "x", "history": [], "scenario": "answered"})
            assert rejected.status_code == 400
        build.assert_not_called()


def test_internal_request_schema_agrees_with_basic_wire_shape():
    schema = json.loads((ROOT / "contracts/v0.1/internal_query_request.schema.json").read_text())
    validator = Draft202012Validator(schema)
    assert validator.is_valid({"question": "Kiểm thử", "history": []})
    assert not validator.is_valid({"question": "Kiểm thử", "history": [], "scenario": "answered"})
