"""VLRA-37: luồng truy xuất trong E2E MVP, ghép giống team2_rag.runtime.build_runtime.

Corpus thật (chunks.jsonl) → BM25 save/load → Dense (Qdrant in-memory, embedder băm giả vì không tải model)
→ HybridRetriever → RAGPipeline của Team 2 (reranker + LLM giả). Chỉ model là giả; index, manifest, RRF,
kiểm tra hợp đồng và trích dẫn là code thật.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

DEPS = ("bm25s", "underthesea", "numpy", "qdrant_client", "jsonschema")
HAS_DEPS = all(importlib.util.find_spec(m) for m in DEPS)
ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "data/doanh-nghiep/processed/chunks.jsonl"
META = ("chunk_id", "document_id", "article_id", "document_title", "article", "clause", "point", "source_url")
QUESTIONS = (
    "Doanh nghiệp tư nhân là gì?",
    "Hồ sơ đăng ký thành lập công ty trách nhiệm hữu hạn gồm những gì?",
    "Công ty cổ phần phải có tối thiểu bao nhiêu cổ đông?",
    "Thời hạn góp vốn khi đăng ký thành lập doanh nghiệp là bao lâu?",
    "Quyền của thành viên hợp danh",
)


@unittest.skipUnless(HAS_DEPS, "requires " + ", ".join(DEPS))
class RetrievalE2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from qdrant_client import QdrantClient
        from team1_data.retrieval import BM25Retriever, DenseRetriever, HybridRetriever
        from team2_rag.pipeline import BM25SearchAdapter
        from test_dense_retrieval import FakeEmbedder

        cls.tmp = tempfile.TemporaryDirectory()
        bm_dir, dense_dir = Path(cls.tmp.name) / "bm25" / "e2e", Path(cls.tmp.name) / "dense" / "e2e"
        BM25Retriever.from_jsonl(CHUNKS).save(bm_dir, index_version="e2e")
        cls.client = QdrantClient(":memory:")
        DenseRetriever.from_jsonl(CHUNKS, embedder=FakeEmbedder(), client=cls.client, index_version="e2e").save(dense_dir)
        cls.manifests = [json.loads((d / "index_manifest.json").read_text(encoding="utf-8")) for d in (bm_dir, dense_dir)]
        cls.bm25 = BM25Retriever.load(bm_dir, CHUNKS)
        cls.dense = DenseRetriever.connect(dense_dir, FakeEmbedder(), client=cls.client)
        cls.hybrid = HybridRetriever(BM25SearchAdapter(cls.bm25), cls.dense)
        cls.corpus = {c["chunk_id"]: c for c in map(json.loads, CHUNKS.read_text(encoding="utf-8").splitlines())}

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.tmp.cleanup()

    def test_indexes_satisfy_runtime_consistency_check(self):
        bm, dense = self.manifests
        self.assertEqual(bm["index_version"], dense["index_version"])
        self.assertEqual(set(bm["chunk_ids"]), set(dense["chunk_ids"]))

    def test_hybrid_output_matches_public_retrieval_contract(self):
        from jsonschema import Draft202012Validator
        schema = json.loads((ROOT / "contracts/v0.1/retrieval_output.schema.json").read_text(encoding="utf-8"))
        for q in QUESTIONS:
            with self.subTest(q=q):
                out = self.hybrid.retrieve(q, top_k=20)
                Draft202012Validator(schema).validate(out)
                self.assertEqual(len(out["results"]), 20)
                self.assertEqual([r["rank"] for r in out["results"]], list(range(1, 21)))
                for row in out["results"]:
                    src = self.corpus[row["chunk_id"]]
                    self.assertEqual(row["retrieval_method"], "hybrid_rrf")
                    self.assertIn(src["legal_status"], ("con_hieu_luc", "het_hieu_luc_mot_phan"))
                    self.assertEqual({k: row[k] for k in META}, {k: src[k] for k in META})

    def test_pipeline_answers_with_citation_from_retrieved_chunk(self):
        from team2_rag.llm.fake import FakeLLMProvider
        from team2_rag.llm.service import LLMService
        from team2_rag.pipeline import RAGPipeline
        from team2_rag.reranker import rerank_with_details

        def scorer(pairs):  # điểm = số âm tiết câu hỏi xuất hiện trong chunk (thay cho BGE)
            return [float(sum(w in passage.lower() for w in q.lower().split())) for q, passage in pairs]

        for q in QUESTIONS:
            with self.subTest(q=q):
                top = rerank_with_details(self.hybrid.retrieve(q, top_k=20), scorer=scorer, strict=True).output["results"][0]
                reply = {"status": "answered", "answer": "Trả lời kiểm thử [C1].",
                         "citations": [{"citation_id": "C1", **{k: top[k] for k in META}}]}
                provider = FakeLLMProvider([reply])
                result = RAGPipeline(self.hybrid, LLMService(provider), scorer=scorer).query(q, [])
                self.assertEqual(result["status"], "answered")
                cited = result["citations"][0]
                self.assertEqual({k: cited[k] for k in META}, {k: self.corpus[top["chunk_id"]][k] for k in META})
                self.assertIn("chunk_id=" + top["chunk_id"], provider.calls[0][0].user)


if __name__ == "__main__":
    unittest.main()
