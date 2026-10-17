"""Hằng số và hàm dùng chung cho các nhánh retrieval (BM25, Dense, sau này Hybrid)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path

DEFAULT_CHUNKS = Path("data/doanh-nghiep/processed/chunks.jsonl")
DEFAULT_LEGAL_STATUS = ("con_hieu_luc", "het_hieu_luc_mot_phan")
MAX_QUESTION_CHARS = 4000
MAX_TOP_K = 50
MANIFEST = "index_manifest.json"
DEFAULT_QDRANT_URL = "http://localhost:6333"

# Trường gửi sang Team 2 (contract v0.1), sao chép nguyên từ chunk.
OUTPUT_FIELDS = (
    "chunk_id", "document_id", "article_id", "content", "document_title",
    "article", "clause", "point", "source_url",
)


def search_text(chunk: Mapping) -> str:
    return chunk["context_header"] + "\n" + chunk["content"]


def load_chunks(path: str | Path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def filter_chunks(chunks: Iterable[Mapping], legal_status: Iterable[str]) -> list[dict]:
    """Giữ chunk có legal_status được phép; rỗng hoặc trùng chunk_id thì raise."""
    allowed = set(legal_status)
    kept = [dict(c) for c in chunks if c.get("legal_status") in allowed]
    if not kept:
        raise ValueError("no chunk left to index after the legal_status filter")
    ids = [c["chunk_id"] for c in kept]
    if len(set(ids)) != len(ids):
        raise ValueError("chunk_id must be unique")
    return kept


def ids_hash(chunk_ids: Iterable[str]) -> str:
    return hashlib.sha256("\n".join(chunk_ids).encode("utf-8")).hexdigest()


def validate_query(question: object, top_k: object) -> str:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string")
    question = question.strip()
    if len(question) > MAX_QUESTION_CHARS:
        raise ValueError(f"question must not exceed {MAX_QUESTION_CHARS} characters")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= MAX_TOP_K:
        raise ValueError(f"top_k must be an integer from 1 to {MAX_TOP_K}")
    return question


def output_row(chunk: Mapping, score: float, rank: int, method: str) -> dict:
    row = {f: chunk[f] for f in OUTPUT_FIELDS}
    row.update(score=score, rank=rank, retrieval_method=method)
    return row
