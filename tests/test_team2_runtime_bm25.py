"""RAG_BM25_ONLY: runtime nhẹ chỉ BM25, không rerank, không cần Qdrant/BGE; không gọi mạng."""
import tempfile
import unittest
from pathlib import Path

from team2_rag.runtime import build_runtime

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


if __name__ == "__main__":
    unittest.main()
