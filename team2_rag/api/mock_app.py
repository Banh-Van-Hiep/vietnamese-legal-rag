"""Self-contained HTTP mock for Team 3 E2E testing (VLRA-44).

Provides deterministic fixtures matching contracts without requiring live models or indexes.
"""
from __future__ import annotations

import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

MOCK_ARTICLE = {
    "document_id": "mock_v1",
    "document_title": "Văn bản giả lập dùng để kiểm thử",
    "article_id": "art1",
    "article": "Điều 1 (giả lập)",
    "content": "Điều 1 (giả lập)\n1. Đây là nguyên văn Điều giả lập dùng để kiểm thử tích hợp.\n2. Nội dung này không phải quy định pháp luật.",
    "source_url": "https://example.com/mock-law",
}


def create_mock_app() -> FastAPI:
    app = FastAPI(title="Legal RAG internal service — MOCK fixtures", version="0.1.0")

    @app.middleware("http")
    async def add_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-RAG-Mode"] = "mock"
        req_id = request.headers.get("x-request-id", "mock-req-id")
        response.headers["X-Request-ID"] = req_id
        return response

    @app.get("/internal/v1/health")
    def health():
        return {"status": "up"}

    @app.get("/internal/v1/ready")
    def ready():
        return {"status": "ready"}

    @app.post("/internal/v1/query")
    async def query(request: Request):
        scenario = os.environ.get("RAG_MOCK_SCENARIO", "answered")
        if scenario == "insufficient_context":
            return JSONResponse({
                "status": "insufficient_context",
                "answer": "Đây là dữ liệu giả lập: tài liệu chưa đủ căn cứ để trả lời.",
                "citations": [],
            })
        return JSONResponse({
            "status": "answered",
            "answer": "Đây là câu trả lời giả lập để kiểm thử API/UI, không phải tư vấn pháp luật. Đoạn mẫu được dẫn tại [C1].",
            "citations": [{
                "citation_id": "C1",
                "chunk_id": "mock_v1__art1__k1__0",
                "document_id": "mock_v1",
                "document_title": "Văn bản giả lập dùng để kiểm thử",
                "article_id": "art1",
                "article": "Điều 1 (giả lập)",
                "clause": "Khoản 1",
                "point": None,
                "source_url": "https://example.com/mock-law",
            }],
        })

    @app.get("/internal/v1/documents/{document_id}/articles/{article_id}")
    def get_article(document_id: str, article_id: str):
        if document_id != MOCK_ARTICLE["document_id"]:
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "DOCUMENT_NOT_FOUND", "message": "Văn bản không tồn tại", "retryable": False}},
            )
        if article_id != MOCK_ARTICLE["article_id"]:
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "ARTICLE_NOT_FOUND", "message": "Điều luật không tồn tại", "retryable": False}},
            )
        return JSONResponse(MOCK_ARTICLE)

    return app
