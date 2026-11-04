"""Load existing indexes/models once; configuration is internal to Python.

LLM settings stay owned by config/settings.py (VLRA-46), generation and
provider errors by answer.py/llm (VLRA-39/47). No fake fallback is configured.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from .config.settings import ConfigError, load_settings, read_dotenv
from .llm.factory import create_llm_service
from .llm.tokens import token_budget_from_settings
from .pipeline import BM25SearchAdapter, RAGPipeline
from .reranker import BGEScorer

log = logging.getLogger(__name__)


def _flag(env, key, default):
    return env.get(key, default).strip().lower() in ("true", "1")


@dataclass
class Runtime:
    pipeline: RAGPipeline
    client: object
    _closed: bool = field(default=False, init=False, repr=False, compare=False)

    def close(self):
        """Idempotent: the underlying client is closed at most once, however many callers close the runtime."""
        if self._closed:
            return
        self._closed = True
        self.client.close()


def build_runtime(env=None) -> Runtime:
    env = {**read_dotenv(".env"), **os.environ} if env is None else env
    required = ("RAG_BM25_INDEX", "RAG_DENSE_INDEX")
    if any(not env.get(k, "").strip() for k in required):
        raise ConfigError("Set RAG_BM25_INDEX and RAG_DENSE_INDEX to existing Team 1 indexes")
    bm_dir, dense_dir = (Path(env[k]) for k in required)
    bm = json.loads((bm_dir / "index_manifest.json").read_text(encoding="utf-8"))
    dense = json.loads((dense_dir / "index_manifest.json").read_text(encoding="utf-8"))
    if (bm["index_version"] != dense["index_version"] or
            set(bm["chunk_ids"]) != set(dense["chunk_ids"])):
        raise ConfigError("BM25 and Dense must use the same index version and chunk IDs")
    # Validate LLM before expensive model downloads.
    settings = load_settings(env=env)
    llm = create_llm_service(settings)
    budget = token_budget_from_settings(settings) if settings.context_window_tokens else None
    from qdrant_client import QdrantClient
    from team1_data.retrieval import BM25Retriever, DenseRetriever, HybridRetriever, SentenceTransformerEmbedder
    try:
        from team1_data.retrieval.hybrid import DEFAULT_WEIGHTS
    except ImportError:
        DEFAULT_WEIGHTS = (0.5, 1.0)

    client = (QdrantClient(path=env["RAG_QDRANT_PATH"]) if env.get("RAG_QDRANT_PATH") else
              QdrantClient(url=env.get("RAG_QDRANT_URL", "http://localhost:6333"), timeout=30))
    try:
        embedder = SentenceTransformerEmbedder(
            name=dense["embedding_model"], revision=dense["embedding_revision"],
            query_prefix=dense.get("query_prefix", ""), passage_prefix=dense.get("passage_prefix", ""),
            device="cpu",
        )
        chunks = env.get("RAG_CHUNKS", "data/doanh-nghiep/processed/chunks.jsonl")
        sparse = BM25Retriever.load(bm_dir, chunks)
        vectors = DenseRetriever.connect(dense_dir, embedder, client=client)
        retrieval_timeout = float(env.get("RAG_RETRIEVAL_TIMEOUT", "35"))
        # Trọng số đặt tường minh (mặc định = retrieval_v2 của Team 1) để log và report ghi đúng giá trị đang chạy.
        weights = (float(env.get("RAG_BM25_WEIGHT", DEFAULT_WEIGHTS[0])), float(env.get("RAG_DENSE_WEIGHT", DEFAULT_WEIGHTS[1])))
        hybrid = HybridRetriever(BM25SearchAdapter(sparse), vectors, weights=weights, timeout=retrieval_timeout)
        try:
            embedder.embed_query("Khởi động mô hình embedding")
        except Exception:
            pass
        truncate = _flag(env, "RAG_RERANK_TRUNCATE", "false")  # chưa đo lợi ích: mặc định giữ nguyên (xem optimal_rag_configuration.md)
        scorer = BGEScorer(truncate=truncate)
        scorer([("Khởi động mô hình", "Đây là nội dung khởi động mô hình.")])
        top_k = int(env.get("RAG_TOP_K", "10"))
        strict_rerank = _flag(env, "RAG_STRICT_RERANK", "false")
        rerank_enabled = _flag(env, "RAG_RERANK", "true")
        rerank_timeout = float(env.get("RAG_RERANK_TIMEOUT_SECONDS", "4"))
        pipeline = RAGPipeline(hybrid, llm, scorer=scorer, top_k=top_k, settings=settings, token_budget=budget,
                               strict_rerank=strict_rerank, rerank_enabled=rerank_enabled, rerank_timeout=rerank_timeout)
        log.info("rag_config bm25_dense_weights=%s:%s top_k=%d rerank=%s truncate=%s strict_rerank=%s rerank_timeout=%ss",
                 *weights, top_k, rerank_enabled, truncate, strict_rerank, rerank_timeout)
        return Runtime(pipeline, client)
    except BaseException:
        client.close()
        raise
