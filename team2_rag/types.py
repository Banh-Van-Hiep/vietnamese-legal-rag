"""Python typing for the existing shared contract; JSON Schema is authoritative."""

from typing import Literal, TypedDict


class HistoryMessage(TypedDict):
    role: Literal["user", "assistant"]
    content: str


class Citation(TypedDict):
    citation_id: str
    chunk_id: str
    document_id: str
    article_id: str
    document_title: str
    article: str
    clause: str | None
    point: str | None
    source_url: str


class RAGResponse(TypedDict):
    status: Literal["answered", "insufficient_context"]
    answer: str
    citations: list[Citation]
