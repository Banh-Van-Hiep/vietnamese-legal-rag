"""Dense retriever trên Qdrant, theo docs/team1_data/dense-retrieval-proposal.md mục 4.

Build: encode chunk → upsert vào collection legal_chunks_{index_version}
(named vector "dense", cosine, payload = metadata chunk) → chuyển alias legal_chunks.
Trả kết quả đúng contracts/v0.1/retrieval_output.schema.json với retrieval_method = "dense".

    python -m team1_data.retrieval dense-build --out data/index/dense/2026-10-17-01
    python -m team1_data.retrieval dense-query --index data/index/dense/2026-10-17-01 "câu hỏi"
"""

from __future__ import annotations

import json
import math
import uuid
import warnings
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from qdrant_client import QdrantClient, models

from .common import (
    DEFAULT_CHUNKS, DEFAULT_LEGAL_STATUS, DEFAULT_QDRANT_URL, MANIFEST, filter_chunks, ids_hash,
    load_chunks, output_row, search_text, validate_query,
)
from .embedding import Embedder, l2_normalize
from .errors import RetrievalUnavailableError

COLLECTION_ALIAS = "legal_chunks"
VECTOR_NAME = "dense"
UPSERT_BATCH = 256
KEYWORD_INDEXES = ("legal_status", "document_type", "document_id", "document_key")


def collection_name(index_version: str) -> str:
    return f"{COLLECTION_ALIAS}_{index_version}"


def point_id(chunk_id: str) -> str:
    """ID xác định từ chunk_id, nên upsert lại không tạo bản trùng."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def _qdrant(what: str, fn, *args, **kwargs):
    """Gọi Qdrant; mọi lỗi kết nối/collection thành RetrievalUnavailableError."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        raise RetrievalUnavailableError(f"Qdrant {what} failed ({type(exc).__name__}: {exc})") from exc


class DenseRetriever:
    """Tìm kiếm ngữ nghĩa trên các chunk còn hiệu lực, vector lưu trong Qdrant."""

    def __init__(
        self,
        chunks: Iterable[Mapping],
        embedder: Embedder,
        *,
        client: QdrantClient | None = None,
        index_version: str = "dev",
        legal_status: Iterable[str] = DEFAULT_LEGAL_STATUS,
    ) -> None:
        """Build index: encode chunk và ghi vào collection mới; collection đã tồn tại thì raise."""
        self.chunks = filter_chunks(chunks, legal_status)
        self.embedder = embedder
        self.client = client if client is not None else QdrantClient(":memory:")
        self.index_version = index_version
        self.collection = collection_name(index_version)
        self.legal_status = sorted(set(legal_status))
        self.embeddings = l2_normalize(embedder.embed_passages([search_text(c) for c in self.chunks]))
        if self.embeddings.shape != (len(self.chunks), embedder.dim):
            raise ValueError(f"embedder returned shape {self.embeddings.shape}, expected "
                             f"({len(self.chunks)}, {embedder.dim})")
        self._build_collection()

    def _build_collection(self) -> None:
        client, name = self.client, self.collection
        if _qdrant("collection_exists", client.collection_exists, name):
            raise ValueError(f"collection {name} already exists; build a new index_version or use connect()")
        _qdrant("create_collection", client.create_collection, name, vectors_config={
            VECTOR_NAME: models.VectorParams(size=self.embedder.dim, distance=models.Distance.COSINE),
        })
        with warnings.catch_warnings():
            # Qdrant local (":memory:" / path) bỏ qua payload index và cảnh báo; server thì dùng.
            warnings.filterwarnings("ignore", message="Payload indexes have no effect")
            for field in KEYWORD_INDEXES:
                _qdrant("create_payload_index", client.create_payload_index,
                        name, field, models.PayloadSchemaType.KEYWORD)
            _qdrant("create_payload_index", client.create_payload_index,
                    name, "effective_date", models.PayloadSchemaType.DATETIME)
        for start in range(0, len(self.chunks), UPSERT_BATCH):
            points = [
                models.PointStruct(id=point_id(c["chunk_id"]), vector={VECTOR_NAME: v.tolist()}, payload=c)
                for c, v in zip(self.chunks[start:start + UPSERT_BATCH], self.embeddings[start:start + UPSERT_BATCH])
            ]
            _qdrant("upsert", client.upsert, name, points=points, wait=True)
        count = _qdrant("count", client.count, name, exact=True).count
        if count != len(self.chunks):
            raise RetrievalUnavailableError(f"collection {name} has {count} points, expected {len(self.chunks)}")
        _qdrant("update_collection_aliases", client.update_collection_aliases, change_aliases_operations=[
            models.CreateAliasOperation(create_alias=models.CreateAlias(collection_name=name, alias_name=COLLECTION_ALIAS)),
        ])

    @classmethod
    def from_jsonl(cls, path: str | Path = DEFAULT_CHUNKS, *, embedder: Embedder, **kwargs) -> "DenseRetriever":
        return cls(load_chunks(path), embedder, **kwargs)

    @property
    def chunk_ids(self) -> list[str]:
        return [c["chunk_id"] for c in self.chunks]

    def save(self, index_dir: str | Path) -> Path:
        """Lưu cache embedding và manifest; vector và metadata phục vụ truy vấn nằm trong Qdrant."""
        index_dir = Path(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        np.save(index_dir / "embeddings.npy", self.embeddings)
        (index_dir / "chunk_ids.json").write_text(json.dumps(self.chunk_ids, ensure_ascii=False), encoding="utf-8")
        manifest = {
            "index_version": self.index_version,
            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "collection": self.collection,
            "vector_name": VECTOR_NAME, "distance": "cosine",
            "embedding_model": self.embedder.name,
            "embedding_revision": self.embedder.revision,
            "embedding_dim": self.embedder.dim,
            "query_prefix": getattr(self.embedder, "query_prefix", ""),
            "passage_prefix": getattr(self.embedder, "passage_prefix", ""),
            "legal_status": self.legal_status,
            "chunk_count": len(self.chunks),
            "chunk_ids_sha256": ids_hash(self.chunk_ids),
            "chunk_ids": self.chunk_ids,
        }
        (index_dir / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
        return index_dir

    @classmethod
    def connect(
        cls,
        index_dir: str | Path,
        embedder: Embedder,
        *,
        client: QdrantClient | None = None,
        url: str = DEFAULT_QDRANT_URL,
    ) -> "DenseRetriever":
        """Nối vào collection đã build; lệch model, số point hoặc tập chunk_id thì raise."""
        try:
            manifest = json.loads((Path(index_dir) / MANIFEST).read_text(encoding="utf-8"))
            name, ids = manifest["collection"], manifest["chunk_ids"]
        except (OSError, ValueError, KeyError) as exc:
            raise RetrievalUnavailableError(f"cannot load dense index manifest ({type(exc).__name__})") from exc
        if ids_hash(ids) != manifest.get("chunk_ids_sha256"):
            raise RetrievalUnavailableError("dense index manifest is corrupted (chunk_ids hash mismatch)")
        expected = (manifest.get("embedding_model"), manifest.get("embedding_revision"), manifest.get("embedding_dim"))
        if (embedder.name, embedder.revision, embedder.dim) != expected:
            raise RetrievalUnavailableError(
                f"embedder {embedder.name}@{embedder.revision} (dim {embedder.dim}) does not match the index "
                f"({expected[0]}@{expected[1]}, dim {expected[2]})")
        client = client if client is not None else QdrantClient(url=url)
        if not _qdrant("collection_exists", client.collection_exists, name):
            raise RetrievalUnavailableError(f"collection {name} does not exist")
        points, offset, stored = [], None, set()
        while True:
            points, offset = _qdrant("scroll", client.scroll, name, limit=1024, offset=offset,
                                     with_payload=["chunk_id"], with_vectors=False)
            stored.update(p.payload["chunk_id"] for p in points)
            if offset is None:
                break
        if stored != set(ids):
            raise RetrievalUnavailableError(
                f"collection {name} does not match the manifest ({len(stored)} points, {len(ids)} chunk_id)")
        self = cls.__new__(cls)
        self.embedder, self.client = embedder, client
        self.index_version, self.collection = manifest["index_version"], name
        self.legal_status = manifest["legal_status"]
        self.chunks = [{"chunk_id": i} for i in ids]
        self.embeddings = None
        return self

    def _search(self, question: str, limit: int = 100) -> list[dict]:
        """Lấy danh sách candidate Dense cho Hybrid RRF."""
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 to 100")

        question = validate_query(question, min(limit, 50))
        vector = l2_normalize(self.embedder.embed_query(question))

        hits = _qdrant(
            "query_points",
            self.client.query_points,
            self.collection,
            query=vector.tolist(),
            using=VECTOR_NAME,
            limit=limit,
            with_payload=True,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="legal_status",
                        match=models.MatchAny(any=self.legal_status),
                    ),
                ],
            ),
        ).points

        results = []
        for hit in hits:
            score = float(hit.score)
            if not math.isfinite(score):
                continue

            results.append(
                output_row(
                    hit.payload,
                    score,
                    len(results) + 1,
                    "dense",
                )
            )

        return results

    def retrieve(self, question: str, top_k: int = 20) -> dict:
        """Trả {question, results}; dense luôn có hàng xóm gần nhất nên không tự cắt theo ngưỡng cosine."""
        question = validate_query(question, top_k)
        results = self._search(question, limit=top_k)
        return {"question": question, "results": results}
