"""VLRA-53: cấu hình Retrieval v2 đã chọn phải chạy được với API hiện tại, không đổi contract."""

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "team1_data/retrieval/retrieval_v2.json").read_text(encoding="utf-8"))
HAS_DEPS = all(importlib.util.find_spec(m) for m in ("bm25s", "underthesea", "jsonschema"))


@unittest.skipUnless(HAS_DEPS, "requires bm25s, underthesea, jsonschema")
class RetrievalV2ConfigTest(unittest.TestCase):
    def test_config_matches_runtime_defaults(self):
        import inspect
        from team1_data.retrieval import hybrid
        from team1_data.retrieval.bm25 import BM25Retriever
        from team1_data.retrieval.common import DEFAULT_LEGAL_STATUS
        from team1_data.retrieval.embedding import DEFAULT_MODEL

        bm25 = inspect.signature(BM25Retriever.__init__).parameters
        hyb = inspect.signature(hybrid.HybridRetriever.__init__).parameters
        self.assertEqual((bm25["k1"].default, bm25["b"].default), (CONFIG["bm25"]["k1"], CONFIG["bm25"]["b"]))
        self.assertEqual(hyb["rrf_k"].default, CONFIG["hybrid"]["rrf_k"])
        self.assertEqual(list(hyb["weights"].default), CONFIG["hybrid"]["weights"])
        self.assertEqual(hybrid.CANDIDATE_LIMIT, CONFIG["hybrid"]["candidate_limit"])
        self.assertEqual(DEFAULT_MODEL, CONFIG["dense"]["embedding_model"])
        self.assertEqual(list(DEFAULT_LEGAL_STATUS), CONFIG["legal_status"])

    def test_config_builds_contract_valid_hybrid(self):
        from jsonschema import Draft202012Validator
        from team1_data.retrieval.bm25 import BM25Retriever
        from team1_data.retrieval.common import load_chunks
        from team1_data.retrieval.hybrid import HybridRetriever

        chunks = load_chunks(ROOT / "data/doanh-nghiep/processed/chunks.jsonl")[:300]
        bm25 = BM25Retriever(chunks, k1=CONFIG["bm25"]["k1"], b=CONFIG["bm25"]["b"],
                             legal_status=CONFIG["legal_status"])
        h = CONFIG["hybrid"]
        retriever = HybridRetriever(bm25, bm25, rrf_k=h["rrf_k"], weights=h["weights"])
        out = retriever.retrieve("Vốn điều lệ công ty cổ phần", top_k=CONFIG["top_k"])
        schema = json.loads((ROOT / "contracts/v0.1/retrieval_output.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(out)
        self.assertEqual(len(out["results"]), CONFIG["top_k"])


if __name__ == "__main__":
    unittest.main()
