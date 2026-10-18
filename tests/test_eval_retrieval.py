"""Independent metric examples; no retrieval dependencies or network required."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.eval_retrieval import evaluate, metrics, percentile, validate_cases


def row(cid, rank, score=1.0):
    return dict(chunk_id=cid, document_id="doc-v1", article_id="dieu-1", content="content",
                document_title="Document", article="Điều 1", clause=None, point=None,
                source_url="https://example.com/law", score=score, rank=rank, retrieval_method="bm25")


class MetricTests(unittest.TestCase):
    def test_partial_recall_and_first_relevant_rr(self):
        self.assertEqual(metrics(["x", "b", "a"], ["a", "b"]),
                         {"recall_at_5": 1.0, "recall_at_20": 1.0, "rr_at_10": 0.5})
        result = metrics(["x"] * 4 + ["a"] + ["b"], ["a", "b"])
        self.assertEqual(result["recall_at_5"], 0.5)
        self.assertEqual(result["rr_at_10"], 0.2)

    def test_cutoff_and_miss(self):
        self.assertEqual(metrics(["x"] * 10 + ["a"], ["a"])["rr_at_10"], 0)
        self.assertEqual(metrics([], ["a"])["recall_at_20"], 0)

    def test_empty_gold_is_not_perfect_recall(self):
        self.assertTrue(all(v is None for v in metrics(["a"], []).values()))

    def test_percentile_linear_interpolation(self):
        self.assertEqual(percentile([1, 2, 3, 4], 0.5), 2.5)
        self.assertAlmostEqual(percentile([1, 2, 3, 4], 0.95), 3.85)
        self.assertIsNone(percentile([], 0.95))

    def test_macro_average_and_empty_gold_denominator(self):
        class Retriever:
            def retrieve(self, question, top_k):
                return {"question": question, "results": [row("a", 1)]}
        cases = [dict(id="1", question="one", gold_chunk_ids=["a", "b"]),
                 dict(id="2", question="two", gold_chunk_ids=["a"]),
                 dict(id="3", question="three", gold_chunk_ids=[])]
        result = evaluate(Retriever(), cases, method="bm25")
        self.assertEqual(result["metrics"]["recall_at_20"], 0.75)
        self.assertEqual(result["counts"]["scored"], 2)
        self.assertEqual(result["counts"]["empty_gold"], 1)

    def test_errors_are_reported_and_run_fails(self):
        class Broken:
            def retrieve(self, question, top_k):
                raise RuntimeError("test failure")
        result = evaluate(Broken(), [dict(id="1", question="one", gold_chunk_ids=["a"])], method="bm25")
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["counts"]["errors"], 1)
        self.assertEqual(result["counts"]["scored"], 0)
        self.assertIsNone(result["metrics"]["recall_at_20"])

    def test_duplicate_candidate_is_error_not_extra_hit(self):
        class Duplicate:
            def retrieve(self, question, top_k):
                return {"question": question, "results": [row("a", 1), row("a", 2)]}
        result = evaluate(Duplicate(), [dict(id="1", question="one", gold_chunk_ids=["a"])], method="bm25")
        self.assertEqual(result["counts"]["errors"], 1)

    def test_unknown_gold_duplicate_cases_and_invalid_status_are_rejected(self):
        cases = [dict(id="1", question="one", gold_chunk_ids=["missing"], expected_status="answered")]
        with self.assertRaises(ValueError):
            validate_cases(cases, {"a"})
        cases[0]["gold_chunk_ids"] = ["a"]
        with self.assertRaises(ValueError):
            validate_cases(cases + cases, {"a"})
        cases[0]["expected_status"] = "bad"
        with self.assertRaises(ValueError):
            validate_cases(cases, {"a"})

    def test_cli_setup_failure_still_writes_json_and_nonzero_exit(self):
        from scripts.eval_retrieval import main
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "result.json"
            code = main(["--method", "bm25", "--golden", str(Path(temp) / "missing.json"),
                         "--output", str(output)])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["status"], "BLOCKED")
