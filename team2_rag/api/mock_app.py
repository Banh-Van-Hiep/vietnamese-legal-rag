"""Explicit HTTP mock: same routes/contracts as live, without indexes, models or API keys."""
from __future__ import annotations

import os

from ..articles import ArticleResponse, validate_article_ids
from ..config.settings import ConfigError
from ..errors import ArticleNotFoundError, DocumentNotFoundError
from ..mock import make_mock_response
from ..pipeline import validate_generated_response
from .app import create_app

MOCK_ARTICLE = {
    "document_id": "mock_v1",
    "document_title": "Văn bản giả lập dùng để kiểm thử",
    "article_id": "art1",
    "article": "Điều 1 (giả lập)",
    "content": "Điều 1 (giả lập)\n1. Đây là nguyên văn Điều giả lập dùng để kiểm thử tích hợp.\n2. Nội dung này không phải quy định pháp luật.",
    "source_url": "https://example.com/mock-law",
}


class MockPipeline:
    def __init__(self, scenario="answered"):
        if scenario not in ("answered", "insufficient_context"):
            raise ConfigError("RAG_MOCK_SCENARIO must be answered or insufficient_context")
        self.scenario = scenario

    def query(self, question, history, *, request_id=None):
        return validate_generated_response(make_mock_response(self.scenario))


class MockArticleStore:
    def get_article(self, document_id, article_id):
        validate_article_ids(document_id, article_id)
        if document_id != MOCK_ARTICLE["document_id"]:
            raise DocumentNotFoundError()
        if article_id != MOCK_ARTICLE["article_id"]:
            raise ArticleNotFoundError()
        return ArticleResponse.model_validate(MOCK_ARTICLE).model_dump(mode="json")


def create_mock_app():
    app = create_app(
        pipeline=MockPipeline(os.environ.get("RAG_MOCK_SCENARIO", "answered")),
        article_store=MockArticleStore(),
    )
    app.title = "Legal RAG internal service — MOCK integration fixtures"

    @app.middleware("http")
    async def label_mock(request, call_next):
        response = await call_next(request)
        response.headers["X-RAG-Mode"] = "mock"
        return response

    return app
