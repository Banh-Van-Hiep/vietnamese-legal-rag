"""RAG_BM25_ONLY: runtime nhẹ chỉ BM25, không rerank, không cần Qdrant/BGE; không gọi mạng."""
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from team2_rag.runtime import build_runtime
from team2_rag.verification import verify_response

CHUNKS = Path(__file__).resolve().parents[1] / "data/doanh-nghiep/processed/chunks.jsonl"


class BM25OnlyRuntimeTests(unittest.TestCase):
    def test_builds_without_dense_index_and_never_reranks(self):
        with tempfile.TemporaryDirectory() as tmp:
            small = Path(tmp) / "chunks.jsonl"
            small.write_text("".join(CHUNKS.open(encoding="utf-8").readlines()[:30]), encoding="utf-8")
            runtime = build_runtime({"RAG_BM25_ONLY": "true", "RAG_CHUNKS": str(small), "LLM_PROVIDER": "gemini",
                                     "LLM_MODEL": "m", "GEMINI_API_KEY": "k"})
        self.addCleanup(runtime.close)
        self.assertFalse(runtime.pipeline.rerank_enabled)
        self.assertIsNone(runtime.pipeline.scorer)
        runtime.close()  # client giả phải đóng được, và đóng lặp lại vẫn an toàn
        runtime.close()

    def _bm25_runtime(self, **extra):
        with tempfile.TemporaryDirectory() as tmp:
            small = Path(tmp) / "chunks.jsonl"
            small.write_text("".join(CHUNKS.open(encoding="utf-8").readlines()[:30]), encoding="utf-8")
            runtime = build_runtime({"RAG_BM25_ONLY": "true", "RAG_CHUNKS": str(small), "LLM_PROVIDER": "gemini",
                                     "LLM_MODEL": "m", "GEMINI_API_KEY": "k", **extra})
        self.addCleanup(runtime.close)
        return runtime

    def test_verify_claims_off_by_default(self):
        pipeline = self._bm25_runtime().pipeline
        self.assertIsNone(pipeline.verifier)
        self.assertFalse(pipeline.llm_service.include_claims)

    def test_verify_claims_flag_wires_verifier_and_claims(self):
        pipeline = self._bm25_runtime(RAG_VERIFY_CLAIMS="true").pipeline
        self.assertIs(pipeline.verifier, verify_response)
        self.assertTrue(pipeline.llm_service.include_claims)


class HybridRuntimeRerankTests(unittest.TestCase):
    """Runtime đầy đủ với Qdrant/embedding giả: chỉ nạp BGE khi RAG_RERANK=true."""

    def _build(self, rerank):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        env = {"LLM_PROVIDER": "gemini", "LLM_MODEL": "m", "GEMINI_API_KEY": "k", "RAG_RERANK": rerank}
        for name in ("bm25", "dense"):
            d = Path(tmp.name) / name
            d.mkdir()
            (d / "index_manifest.json").write_text(json.dumps({
                "index_version": "v1", "chunk_ids": ["a"], "embedding_model": "e", "embedding_revision": "r"}))
            env[f"RAG_{name.upper()}_INDEX"] = str(d)
        scorer_cls = mock.MagicMock()
        with mock.patch.dict(sys.modules, {"qdrant_client": types.SimpleNamespace(QdrantClient=mock.MagicMock()),
                                           "team1_data.retrieval": mock.MagicMock()}), \
                mock.patch("team2_rag.runtime.BGEScorer", scorer_cls):
            runtime = build_runtime(env)
        return runtime, scorer_cls

    def test_rerank_off_does_not_load_bge(self):
        runtime, scorer_cls = self._build("false")
        scorer_cls.assert_not_called()
        self.assertIsNone(runtime.pipeline.scorer)
        self.assertFalse(runtime.pipeline.rerank_enabled)

    def test_rerank_on_loads_and_warms_bge(self):
        runtime, scorer_cls = self._build("true")
        scorer_cls.assert_called_once()
        scorer_cls.return_value.assert_called_once()  # warm-up một lần lúc khởi động
        self.assertIs(runtime.pipeline.scorer, scorer_cls.return_value)


if __name__ == "__main__":
    unittest.main()
