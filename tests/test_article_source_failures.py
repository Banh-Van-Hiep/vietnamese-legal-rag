"""VLRA-71/A2: regression tests for Article Store source failures.

IMPORTANT: These tests expose known failures in Team 2's current reader.
Expected until Team 2 approves a fix: the 503 tests FAIL, NOT because
Article Store metadata is wrong, but because the reader falls back to chunks
or reports 500/404. Do not mark these tests as passing without running them.
"""
import json

import pytest
from fastapi.testclient import TestClient

import team2_rag.articles as article_module
from team2_rag.api.app import create_app


@pytest.fixture(autouse=True)
def reset_cache():
    article_module._load_article_cache.cache_clear()
    yield
    article_module._load_article_cache.cache_clear()


def _call(document_id="doc-1-v1", article_id="dieu-1"):
    app = create_app(pipeline=object())
    with TestClient(app) as client:
        return client.get(
            f"/internal/v1/documents/{document_id}/articles/{article_id}",
            headers={"X-Request-ID": "vlra71-source-test"},
        )


def _expected_unavailable(response):
    assert response.status_code == 503, response.text
    assert response.json()["error"]["code"] == "RETRIEVAL_UNAVAILABLE"
    assert response.json()["error"]["retryable"] is True
    assert response.headers["X-Request-ID"] == "vlra71-source-test"


def test_missing_articles_file_reports_503_even_if_chunks_exist(tmp_path, monkeypatch):
    missing = tmp_path / "articles.jsonl"
    chunks = tmp_path / "chunks.jsonl"
    chunks.write_text(json.dumps({
        "document_id": "doc-1-v1", "article_id": "dieu-1", "article": "Điều 1",
        "document_title": "Luật thử", "source_url": "https://example.com",
        "chunk_index": 0, "chunk_id": "doc-1-v1__dieu-1__k0__0", "content": "1. Test",
    }) + "\n", encoding="utf-8")
    monkeypatch.setattr(article_module, "ARTICLES_PATH", missing)
    _expected_unavailable(_call())


def test_corrupt_json_line_reports_503(tmp_path, monkeypatch):
    path = tmp_path / "articles.jsonl"
    path.write_text('{"document_id": "broken",\n', encoding="utf-8")
    monkeypatch.setattr(article_module, "ARTICLES_PATH", path)
    _expected_unavailable(_call())


def test_empty_articles_file_reports_503(tmp_path, monkeypatch):
    path = tmp_path / "articles.jsonl"
    path.write_text("", encoding="utf-8")
    monkeypatch.setattr(article_module, "ARTICLES_PATH", path)
    _expected_unavailable(_call())


def test_real_missing_id_is_still_404_when_store_is_valid(tmp_path, monkeypatch):
    path = tmp_path / "articles.jsonl"
    path.write_text(json.dumps({
        "document_id": "doc-1-v1", "document_title": "Luật thử", "article_id": "dieu-1",
        "article": "Điều 1", "content": "Điều 1. Nội dung thử nghiệm.",
        "source_url": "https://example.com",
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    monkeypatch.setattr(article_module, "ARTICLES_PATH", path)
    response = _call(document_id="doc-absent-v1")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"
    response = _call(article_id="dieu-999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ARTICLE_NOT_FOUND"
