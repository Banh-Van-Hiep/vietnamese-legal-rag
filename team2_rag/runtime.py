"""Load existing indexes/models once; configuration is internal to Python.

LLM settings stay owned by config/settings.py (VLRA-46), generation and
provider errors by answer.py/llm (VLRA-39/47). No fake fallback is configured.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from .config.settings import ConfigError, load_settings, read_dotenv
from .llm.factory import create_llm_service
from .llm.tokens import token_budget_from_settings
from .pipeline import BM25SearchAdapter, RAGPipeline
from .reranker import BGEScorer


@dataclass
class Runtime:
    pipeline: RAGPipeline
    client: object

    def close(self):
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

    client = (QdrantClient(path=env["RAG_QDRANT_PATH"]) if env.get("RAG_QDRANT_PATH") else
              QdrantClient(url=env.get("RAG_QDRANT_URL", "http://localhost:6333"), timeout=5))
    try:
        embedder = SentenceTransformerEmbedder(
            name=dense["embedding_model"], revision=dense["embedding_revision"],
            query_prefix=dense.get("query_prefix", ""), passage_prefix=dense.get("passage_prefix", ""),
            device="cpu",
        )
        chunks = env.get("RAG_CHUNKS", "data/doanh-nghiep/processed/chunks.jsonl")
        sparse = BM25Retriever.load(bm_dir, chunks)
        vectors = DenseRetriever.connect(dense_dir, embedder, client=client)
        hybrid = HybridRetriever(BM25SearchAdapter(sparse), vectors)
        scorer = BGEScorer()
        scorer([("Khởi động mô hình", "Đây là nội dung khởi động mô hình.")])
        pipeline = RAGPipeline(hybrid, llm, scorer=scorer, settings=settings, token_budget=budget)
        return Runtime(pipeline, client)
    except BaseException:
        client.close()
        raise
