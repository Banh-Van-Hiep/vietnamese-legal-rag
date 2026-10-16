"""Build LEGAL CONTEXT from reranked Team 1 candidates (docs/team2_rag/context-builder.md).

Input candidates follow contracts/v0.1/retrieval_output.schema.json (12 fields). The reranker may add
extra keys such as `rerank_score`; they are ignored. Content and metadata are never edited: a candidate
that violates the contract is an error, not something to repair. Each selected chunk gets a temporary
label [C1], [C2]... in selection order; `BuiltContext` keeps label -> trusted source chunk for verifying
the LLM's citations afterwards.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence
from urllib.parse import urlparse

from team2_rag.config.settings import DEFAULT_MAX_CONTEXT_CHARS, DEFAULT_MAX_CONTEXT_CHUNKS
from team2_rag.prompts.render import neutralize_boundary_tags

_ID = re.compile(r"[A-Za-z0-9_-]+")
_METHODS = ("bm25", "dense", "hybrid_rrf")


class ContextBudgetError(ValueError):
    """Prompt cố định (system/question/history) đã chiếm hết budget; không gửi prompt vượt giới hạn."""


class ContextBuildError(ValueError):
    """Candidate vi phạm contract Team 1 -> Team 2 (input nội bộ sai, không phải lỗi LLM)."""


@dataclass(frozen=True)
class ContextChunk:
    label: str  # "C1", "C2", ... (nhãn tạm của lượt này)
    chunk_id: str
    document_id: str
    article_id: str
    document_title: str
    article: str
    clause: Optional[str]
    point: Optional[str]
    source_url: str
    content: str

    def source_metadata(self) -> dict[str, Any]:
        """9 trường citation (trừ citation_id) lấy từ nguồn."""
        return {
            "chunk_id": self.chunk_id, "document_id": self.document_id, "article_id": self.article_id,
            "document_title": self.document_title, "article": self.article, "clause": self.clause,
            "point": self.point, "source_url": self.source_url,
        }


@dataclass(frozen=True)
class BuiltContext:
    text: str
    chunks: tuple[ContextChunk, ...]
    skipped_chunk_ids: tuple[str, ...] = ()  # vượt budget; KHÔNG nằm trong prompt nên không được trích dẫn
    budget_unit: str = "chars_approx"  # "tokens" khi đếm bằng TokenCounter; "chars_approx" KHÔNG đáp ứng spec token

    @property
    def is_empty(self) -> bool:
        return not self.chunks

    def by_label(self) -> dict[str, ContextChunk]:
        return {c.label: c for c in self.chunks}


def _string(item: Mapping, name: str, where: str, *, max_len: int, nullable: bool = False,
            pattern: Optional[re.Pattern] = None, single_line: bool = True) -> Optional[str]:
    if name not in item:
        raise ContextBuildError(f"{where} thiếu trường {name}.")
    value = item[name]
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > max_len:
        raise ContextBuildError(f"{where}.{name} không hợp lệ (chuỗi không rỗng, tối đa {max_len} ký tự).")
    if pattern and not pattern.fullmatch(value):
        raise ContextBuildError(f"{where}.{name} phải là ASCII chữ/số/_/-.")
    if single_line and ("\n" in value or "\r" in value):
        raise ContextBuildError(f"{where}.{name} không được chứa xuống dòng.")
    return value


def _validate(index: int, item: Any) -> dict[str, Any]:
    where = f"results[{index}]"
    if not isinstance(item, Mapping):
        raise ContextBuildError(f"{where} phải là object.")
    chunk_id = _string(item, "chunk_id", where, max_len=200)
    where = f"{where} (chunk_id={chunk_id})"
    fields = {
        "chunk_id": chunk_id,
        "document_id": _string(item, "document_id", where, max_len=200, pattern=_ID),
        "article_id": _string(item, "article_id", where, max_len=100, pattern=_ID),
        "document_title": _string(item, "document_title", where, max_len=500),
        "article": _string(item, "article", where, max_len=100),
        "clause": _string(item, "clause", where, max_len=100, nullable=True),
        "point": _string(item, "point", where, max_len=100, nullable=True),
        "source_url": _string(item, "source_url", where, max_len=2048),
        "content": _string(item, "content", where, max_len=20000, single_line=False),
    }
    p = urlparse(fields["source_url"])
    if p.scheme != "https" or not p.netloc:
        raise ContextBuildError(f"{where}.source_url phải là URL HTTPS tuyệt đối.")
    score, rank, method = item.get("score"), item.get("rank"), item.get("retrieval_method")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
        raise ContextBuildError(f"{where}.score phải là số hữu hạn.")
    if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1:
        raise ContextBuildError(f"{where}.rank phải là số nguyên >= 1.")
    if method not in _METHODS:
        raise ContextBuildError(f"{where}.retrieval_method phải thuộc {_METHODS}.")
    return fields


def _render(label: str, f: Mapping[str, Any]) -> str:
    header = (
        f"[{label}] chunk_id={f['chunk_id']} document_id={f['document_id']} article_id={f['article_id']} "
        f"document_title={f['document_title']} article={f['article']} clause={f['clause'] or 'null'} "
        f"point={f['point'] or 'null'} source_url={f['source_url']}"
    )
    return header + "\n" + f["content"]


def build_context(
    results: Sequence[Mapping],
    *,
    max_chunks: int = DEFAULT_MAX_CONTEXT_CHUNKS,
    max_chars: Optional[int] = DEFAULT_MAX_CONTEXT_CHARS,
    token_counter: Optional[Any] = None,
    max_tokens: Optional[int] = None,
) -> BuiltContext:
    """Chọn chunk theo thứ tự reranker (không sắp xếp lại).

    Bỏ chunk trùng chunk_id (giữ bản đầu); chunk không vừa budget thì bỏ qua và xét chunk kế; dừng khi
    đủ `max_chunks`. Mọi candidate trong `results` đều được kiểm tra contract trước khi chọn.

    Budget: nếu có `token_counter` + `max_tokens` thì đếm token (đếm lại toàn bộ context sau khi thêm chunk, trên
    văn bản đã neutralize như lúc render) và bỏ `max_chars`. Nếu không, dùng `max_chars` xấp xỉ (budget_unit
    = "chars_approx").
    """
    if (token_counter is None) != (max_tokens is None):
        raise ValueError("token_counter và max_tokens phải đi cùng nhau")
    if max_tokens is not None and max_tokens < 1:
        raise ContextBudgetError("Không còn token cho legal context.")
    if not isinstance(results, Sequence) or isinstance(results, (str, bytes)):
        raise ContextBuildError("results phải là danh sách.")
    if max_chunks < 1:
        raise ValueError("max_chunks phải >= 1")
    candidates = [_validate(i, item) for i, item in enumerate(results)]
    chunks: list[ContextChunk] = []
    skipped: list[str] = []
    seen: set[str] = set()
    blocks: list[str] = []
    used = 0
    for f in candidates:
        if f["chunk_id"] in seen:
            continue
        seen.add(f["chunk_id"])
        if len(chunks) >= max_chunks:
            skipped.append(f["chunk_id"])
            continue
        label = f"C{len(chunks) + 1}"
        block = _render(label, f)
        if token_counter is not None:
            trial = "\n\n".join(blocks + [block])
            fits = token_counter.count(neutralize_boundary_tags(trial)) <= max_tokens
        else:
            fits = max_chars is None or used + len(block) + (2 if blocks else 0) <= max_chars
        if not fits:
            skipped.append(f["chunk_id"])
            continue
        chunks.append(ContextChunk(label=label, **f))
        blocks.append(block)
        used += len(block) + (2 if len(blocks) > 1 else 0)
    return BuiltContext("\n\n".join(blocks), tuple(chunks), tuple(skipped), "tokens" if token_counter is not None else "chars_approx")
