"""Deterministic fixtures for API/UI development, with no legal claims or network."""

from typing import Literal

from .types import RAGResponse

MockScenario = Literal["answered", "insufficient_context"]


def make_mock_response(scenario: MockScenario = "answered") -> RAGResponse:
    """Create fresh output on each call; never share mutable citation objects."""
    if scenario == "insufficient_context":
        return {
            "status": "insufficient_context",
            "answer": "Đây là dữ liệu giả lập: tài liệu chưa đủ căn cứ để trả lời.",
            "citations": [],
        }
    if scenario != "answered":
        raise ValueError("Mock scenario must be answered or insufficient_context")
    return {
        "status": "answered",
        "answer": "Đây là câu trả lời giả lập để kiểm thử API/UI, không phải tư vấn pháp luật. Đoạn mẫu được dẫn tại [C1].",
        "citations": [{
            "citation_id": "C1",
            "chunk_id": "mock_v1_art1_clause1",
            "document_id": "mock_v1",
            "article_id": "art1",
            "document_title": "Văn bản giả lập dùng để kiểm thử",
            "article": "Điều 1 (giả lập)",
            "clause": "Khoản 1 (giả lập)",
            "point": None,
            "source_url": "https://example.com/mock-law",
        }],
    }
