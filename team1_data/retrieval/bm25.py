"""BM25 retriever, theo docs/team1_data/bm25-proposal.md.

Build index từ chunks.jsonl, lưu ra đĩa, nạp lại, và trả kết quả đúng
contracts/v0.1/retrieval_output.schema.json với retrieval_method = "bm25".

    python -m team1_data.retrieval build --out data/index/bm25/2026-10-17-01
    python -m team1_data.retrieval query --index data/index/bm25/2026-10-17-01 "câu hỏi"
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path

import bm25s

from .errors import RetrievalUnavailableError
from .tokenizer import tokenize_vi

DEFAULT_CHUNKS = Path("data/doanh-nghiep/processed/chunks.jsonl")
DEFAULT_LEGAL_STATUS = ("con_hieu_luc", "het_hieu_luc_mot_phan")
MAX_QUESTION_CHARS = 4000
MAX_TOP_K = 50
MANIFEST = "index_manifest.json"
TOKENIZER_NAME = "tokenize_vi/underthesea"

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


def _ids_hash(chunk_ids: Iterable[str]) -> str:
    return hashlib.sha256("\n".join(chunk_ids).encode("utf-8")).hexdigest()


def _validate_query(question: object, top_k: object) -> str:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string")
    question = question.strip()
    if len(question) > MAX_QUESTION_CHARS:
        raise ValueError(f"question must not exceed {MAX_QUESTION_CHARS} characters")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= MAX_TOP_K:
        raise ValueError(f"top_k must be an integer from 1 to {MAX_TOP_K}")
    return question


class BM25Retriever:
    """Index BM25 (biến thể Lucene) trên các chunk còn hiệu lực."""

    def __init__(
        self,
        chunks: Iterable[Mapping],
        *,
        k1: float = 1.2,
        b: float = 0.75,
        legal_status: Iterable[str] = DEFAULT_LEGAL_STATUS,
    ) -> None:
        allowed = set(legal_status)
        self.chunks = [dict(c) for c in chunks if c.get("legal_status") in allowed]
        if not self.chunks:
            raise ValueError("no chunk left to index after the legal_status filter")
        ids = [c["chunk_id"] for c in self.chunks]
        if len(set(ids)) != len(ids):
            raise ValueError("chunk_id must be unique")
        self.k1, self.b = k1, b
        self.legal_status = sorted(allowed)
        self._bm25 = bm25s.BM25(method="lucene", k1=k1, b=b)
        self._bm25.index([tokenize_vi(search_text(c)) for c in self.chunks], show_progress=False)

    @classmethod
    def from_jsonl(cls, path: str | Path = DEFAULT_CHUNKS, **kwargs) -> "BM25Retriever":
        return cls(load_chunks(path), **kwargs)

    @property
    def chunk_ids(self) -> list[str]:
        return [c["chunk_id"] for c in self.chunks]

    def save(self, index_dir: str | Path, *, index_version: str | None = None) -> Path:
        """Lưu index và manifest; metadata đầy đủ vẫn đọc từ chunks.jsonl khi nạp."""
        index_dir = Path(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        self._bm25.save(str(index_dir))
        manifest = {
            "index_version": index_version or index_dir.name,
            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "method": "lucene", "k1": self.k1, "b": self.b,
            "tokenizer": TOKENIZER_NAME,
            "legal_status": self.legal_status,
            "chunk_count": len(self.chunks),
            "chunk_ids_sha256": _ids_hash(self.chunk_ids),
            "chunk_ids": self.chunk_ids,
        }
        (index_dir / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
        return index_dir

    @classmethod
    def load(cls, index_dir: str | Path, chunks_path: str | Path = DEFAULT_CHUNKS) -> "BM25Retriever":
        """Nạp index đã lưu; lệch với chunk store thì raise, không chạy tiếp."""
        index_dir = Path(index_dir)
        try:
            manifest = json.loads((index_dir / MANIFEST).read_text(encoding="utf-8"))
            model = bm25s.BM25.load(str(index_dir))
            store = {c["chunk_id"]: c for c in load_chunks(chunks_path)}
        except (OSError, ValueError, KeyError) as exc:
            raise RetrievalUnavailableError(f"cannot load BM25 index ({type(exc).__name__})") from exc
        ids = manifest.get("chunk_ids", [])
        missing = [i for i in ids if i not in store]
        if missing or _ids_hash(ids) != manifest.get("chunk_ids_sha256"):
            raise RetrievalUnavailableError(
                f"BM25 index does not match the chunk store ({len(missing)} chunk_id missing)")
        self = cls.__new__(cls)
        self.chunks = [store[i] for i in ids]
        self.k1, self.b = manifest["k1"], manifest["b"]
        self.legal_status = manifest["legal_status"]
        self._bm25 = model
        return self

    def retrieve(self, question: str, top_k: int = 20) -> dict:
        """Trả {question, results}; results rỗng khi không chunk nào trùng từ."""
        question = _validate_query(question, top_k)
        vocab = self._bm25.vocab_dict
        tokens = [t for t in tokenize_vi(question) if t in vocab]
        if not tokens:
            return {"question": question, "results": []}
        k = min(top_k, len(self.chunks))
        docs, scores = self._bm25.retrieve([tokens], k=k, show_progress=False)
        results = []
        for idx, score in zip(docs[0], scores[0]):
            score = float(score)
            if score <= 0 or not math.isfinite(score):
                continue
            chunk = self.chunks[int(idx)]
            row = {f: chunk[f] for f in OUTPUT_FIELDS}
            row.update(score=score, rank=len(results) + 1, retrieval_method="bm25")
            results.append(row)
        return {"question": question, "results": results}

