"""Self-contained HTTP mock for Team 3 E2E testing (VLRA-44).

Provides deterministic fixtures matching contracts without requiring live models or indexes.
"""
from __future__ import annotations

import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from team2_rag.api.handlers import internal_error_payload
from team2_rag.errors import ErrorCode

MOCK_ARTICLE = {
    "document_id": "mock_v1",
    "document_title": "Văn bản giả lập dùng để kiểm thử",
    "article_id": "art1",
    "article": "Điều 1 (giả lập)",
    "content": "Điều 1 (giả lập)\n1. Đây là nguyên văn Điều giả lập dùng để kiểm thử tích hợp.\n2. Nội dung này không phải quy định pháp luật.",
    "source_url": "https://example.com/mock-law",
}

_MOCK_CITATION = {
    "citation_id": "C1",
    "chunk_id": "mock_v1__art1__k1__0",
    "document_id": "mock_v1",
    "document_title": "Văn bản giả lập dùng để kiểm thử",
    "article_id": "art1",
    "article": "Điều 1 (giả lập)",
    "clause": "Khoản 1",
    "point": None,
    "source_url": "https://example.com/mock-law",
}

# Câu trả lời có Markdown (danh sách, bảng) và hai marker, để Team 3 kiểm thử phần hiển thị.
MOCK_MARKDOWN_RESPONSE = {
    "status": "answered",
    "answer": (
        "**Dữ liệu giả lập**, không phải tư vấn pháp luật.\n\n"
        "Các ý chính:\n"
        "- Ý thứ nhất lấy từ Khoản 1 [C1].\n"
        "- Ý thứ hai lấy từ Khoản 2 [C2].\n"
        "  1. Mục con thứ nhất.\n"
        "  2. Mục con thứ hai.\n\n"
        "| Nội dung | Căn cứ |\n"
        "| --- | --- |\n"
        "| Ý thứ nhất | [C1] |\n"
        "| Ý thứ hai | [C2] |"
    ),
    "citations": [
        _MOCK_CITATION,
        {**_MOCK_CITATION, "citation_id": "C2", "chunk_id": "mock_v1__art1__k2__0", "clause": "Khoản 2"},
    ],
}

# Kịch bản lỗi: cùng mã HTTP và body như app thật trả cho Backend (handlers.internal_error_payload).
MOCK_ERRORS = {
    "error_timeout": ErrorCode.UPSTREAM_TIMEOUT,             # 504 LLM_TIMEOUT
    "error_busy": ErrorCode.SERVICE_UNAVAILABLE,             # 503 LLM_UNAVAILABLE (đang xử lý request khác)
    "error_invalid_output": ErrorCode.UPSTREAM_INVALID_RESPONSE,  # 502 INVALID_LLM_OUTPUT
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
        if scenario in MOCK_ERRORS:
            status, body = internal_error_payload(MOCK_ERRORS[scenario])
            return JSONResponse(body, status_code=status)
        if scenario == "answered_markdown":
            return JSONResponse(MOCK_MARKDOWN_RESPONSE)
        if scenario == "insufficient_context":
            return JSONResponse({
                "status": "insufficient_context",
                "answer": "Đây là dữ liệu giả lập: tài liệu chưa đủ căn cứ để trả lời.",
                "citations": [],
            })
        return JSONResponse({
            "status": "answered",
            "answer": "Đây là câu trả lời giả lập để kiểm thử API/UI, không phải tư vấn pháp luật. Đoạn mẫu được dẫn tại [C1].",
            "citations": [_MOCK_CITATION],
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
