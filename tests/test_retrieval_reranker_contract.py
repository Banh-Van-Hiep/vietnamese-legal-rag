"""VLRA-35: đầu ra Retrieval (BM25 / Hybrid RRF) phải qua được kiểm tra đầu vào của Reranker Team 2.

Dùng chunk thật trong data/doanh-nghiep/processed/chunks.jsonl, không mock metadata.
"""

import importlib.util
import unittest
from pathlib import Path

from team1_data.retrieval.common import DEFAULT_LEGAL_STATUS, OUTPUT_FIELDS, load_chunks, output_row

HAS_BM25 = all(importlib.util.find_spec(m) for m in ("bm25s", "underthesea"))
CHUNKS_PATH = Path(__file__).resolve().parents[1] / "data/doanh-nghiep/processed/chunks.jsonl"

try:
    from team2_rag.reranker import RerankInputError, _validate
except Exception:  # Team 2 chưa cài phụ thuộc thì bỏ qua, không giả lập validator.
    _validate = None


@unittest.skipIf(_validate is None, "team2_rag.reranker không import được")
class RetrievalRerankerContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chunks = [c for c in load_chunks(CHUNKS_PATH) if c["legal_status"] in DEFAULT_LEGAL_STATUS]

    def test_every_indexed_chunk_is_accepted_by_reranker(self):
        bad = []
        for chunk in self.chunks:
            try:
                _validate({"question": "câu hỏi", "results": [output_row(chunk, 1.0, 1, "bm25")]})
            except RerankInputError as exc:
                bad.append((chunk["chunk_id"], str(exc)))
        self.assertEqual(bad, [])

    def test_output_row_copies_metadata_unchanged(self):
        chunk = self.chunks[0]
        row = output_row(chunk, 0.5, 1, "dense")
        self.assertEqual({k: row[k] for k in OUTPUT_FIELDS}, {k: chunk[k] for k in OUTPUT_FIELDS})

    @unittest.skipUnless(HAS_BM25, "requires bm25s and underthesea")
    def test_bm25_and_hybrid_output_pass_reranker_validation(self):
        from team1_data.retrieval.bm25 import BM25Retriever
        from team1_data.retrieval.hybrid import HybridRetriever

        bm25 = BM25Retriever(self.chunks[:400])

        class ReversedBM25:  # nhánh thứ hai có thứ tự khác để RRF thực sự gộp
            def _search(self, question, limit=100):
                rows = list(reversed(bm25._search(question, limit)))
                return [dict(r, rank=i, retrieval_method="dense") for i, r in enumerate(rows, 1)]

        hybrid = HybridRetriever(bm25, ReversedBM25())
        for question in ("Doanh nghiệp tư nhân là gì?", "Thành lập công ty cổ phần cần hồ sơ gì?"):
            for retriever in (bm25, hybrid):
                with self.subTest(question=question, retriever=type(retriever).__name__):
                    out = retriever.retrieve(question, top_k=20)
                    self.assertTrue(out["results"])
                    _validate(out)
                    by_id = {c["chunk_id"]: c for c in self.chunks}
                    for row in out["results"]:
                        src = by_id[row["chunk_id"]]
                        self.assertEqual({k: row[k] for k in OUTPUT_FIELDS}, {k: src[k] for k in OUTPUT_FIELDS})


if __name__ == "__main__":
    unittest.main()
